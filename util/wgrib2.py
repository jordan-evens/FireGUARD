#  pywgrib2 5/2020 public domain Wesley Ebisuzaki
#
# provides a simple python interface for reading/writing grib for python based 
# on the fortran wgrib2api
#
#   requirements: python 3.6, numpy (common but not standard), 
#     ctypes and os.path from the standard library

from ctypes import *
import os
import numpy as np
import logging
import common

# load gomp (gnu openmp), gfortran (gnu: IPOLATES, ftp_api), mvec (debian) and 
# wgrib2 libraries, based on your system, run lld wgrib2/wgrib2

# gomp = CDLL("/usr/lib/x86_64-linux-gnu/libgomp.so.1", mode=RTLD_GLOBAL)
# print("loaded gomp library")
# gfortran = CDLL("/lib/x86_64-linux-gnu/libgfortran.so.5", mode=RTLD_GLOBAL)
# print("loaded gfortran library")
# libmvec is needed for ubuntu
# mvec = CDLL("/lib/x86_64-linux-gnu/libmvec.so.1", mode=RTLD_GLOBAL)
# print("loaded mvec library")

# libwgrib2.so must be in same dir as this file, can be link to file
import site
dir=site.getsitepackages()[0]
lib=os.path.join(dir,'libwgrib2.so')
if os.uname().sysname == 'Darwin':
    lib=os.path.join(dir,'libwgrib2.dylib')

try:
    my_wgrib2=CDLL(lib)
except Exception as e:
    print("*** Problem ",e)
    print("*** Will load wgrib2 library in RTLD_LAZY mode")
    my_wgrib2=CDLL(lib, mode=os.RTLD_LAZY)

print("finished loading libraries")

# default global variables

nx = 0
ny = 0
ndata = 0
nmatch = 0
msgno = 0
submsgno = 0
data = None
lat = None
lon = None
matched = []
use_np_nan = True
names='ncep'
# UNDEFINED values from wgrib2.h
UNDEFINED = 9.999e20
UNDEFINED_LOW = 9.9989e20
UNDEFINED_HIGH = 9.9991e20

debug = False
__version__='0.0.11'
print("pywgrib2_s v"+__version__+" 1-15-2021 w. ebisuzaki")


def wgrib2(arg):
    #
    #    call wgrib2
    #        ex.  pywgrib2.wgrib2(["in.grb","-inv","@mem.0"])
    #
    #    uses C calling convention: 1st arg is name of program
    #
    print("wgrib2")
    arg_length = len(arg) + 3
    select_type = (c_char_p * arg_length)
    select = select_type()
    item = "pywgrib2"
    select[0] = item.encode('utf-8')
    item = "-names"
    select[1] = item.encode('utf-8')
    select[2] = names.encode('utf-8')
    
    for key, item in enumerate(arg):
        select[key + 3] = item.encode('utf-8')

    if debug: print("wgrib2 args: ", arg)
    err = my_wgrib2.wgrib2(arg_length, select)
    if debug: print("wgrib2 err=", err)
    return err


def mk_inv(grb_file, inv_file, Use_ncep_table=False, Short=False):
    #
    # make inventory by -Match_inv or -S
    #
    global debug
    cmds = [grb_file, "-rewind_init", grb_file, "-inv", inv_file]

    if Use_ncep_table:
        cmds.append('-set')
        cmds.append('center')
        cmds.append('7')

    if Short == False:
        cmds.append('-Match_inv')
    else:
        cmds.append('-S')

    err = wgrib2(cmds)
    if debug: print("mk_inv ",grb_file,"->",inv_file," err=", err)
    return err


def close(file):
    #
    # close file, does a flush and frees resources
    #
    global debug
    # create byte object
    a = file.encode('utf-8')
    err = my_wgrib2.wgrib2_free_file(a)
    if debug: print("close error ",file," err=", err)
    return err


# inq
#
#  data access options
#    1)  select != '' .. N(.m):byte_location only N is not used
#        a field is selected
#    2)  inv, optional match terms
#    3)  inv == FALSE, optional match terms
#
# register and memory files used by inq()
#
# @mem:10 - used by ftp_api_fn0
# @mem:11 - used by matched inv
# @mem:12 - used by grid metadata
# reg_13  - data (data point values)
# reg_14  - lon
# reg_15  - lat
# reg_16  - sec0
# reg_17  - sec1
# ..
# reg_24  - sec8


def inq(gfile,
        *matches,
        inv='',
        select='',
        Data=False,
        Latlon=False,
        Regex=False,
        grib='',
        Append_grib=False,
        Matched=False,
        sequential=-1,
        var='',
        time0=None,
        ftime='',
        level=''):
    # logging.debug("Start")
    # based on grb2_inq() from ftn wgrib2api

    global nx, ny, ndata, nmatch, msgno, submsgno, matched, data, lat, lon
    global use_np_nan, UNDEFINED_LOW, UNDEFINED_HIGH, debug

    data = None
    lat = None
    lon = None
    matched = []
    
    if inv == '':  # no inventory
        if Regex == False:
            match_option = '-match_fs'
        else:
            match_option = '-match'
    else:  # use inventory
        if Regex == False:
            match_option = '-fgrep'
        else:
            match_option = '-egrep'

    if select != '':  # selected field, use -d, sequential not valid
        if Matched != False:
            cmds = [
                gfile, "-d", select, "-last", "@mem:11", "-print_out", ":",
                "@mem:11", "-S", "-last", "@mem:11", "-nl_out", "@mem:11",
                "-ftn_api_fn0", "-last0", "@mem:10", "-inv", "/dev/null"
            ]
        else:
            cmds = [
                gfile, "-d", select, "-ftn_api_fn0", "-last0", "@mem:10",
                "-inv", "/dev/null"
            ]
    elif inv != '':  # use inventory
        if Matched != False:
            cmds = [
                gfile, "-i_file", inv, "-last", "@mem:11", "-ftn_api_fn0",
                "-last0", "@mem:10", "-inv", "/dev/null", "-print_out", ":",
                "@mem:11", "-S", "-last", "@mem:11", "-nl_out", "@mem:11"
            ]
        else:
            cmds = [
                gfile, "-i_file", inv, "-ftn_api_fn0", "-last0", "@mem:10",
                "-inv", "/dev/null"
            ]
        if sequential <= 0:
            cmds.append('-rewind_init')
            cmds.append(inv)
        if sequential >= 0:
            cmds.append('-end')
        for m in matches:
            cmds.append(match_option)
            cmds.append(m)
    else:  # no inventory
        if Matched != False:
            cmds = [
                gfile, "-last", "@mem:11", "-ftn_api_fn0", "-last0", "@mem:10",
                "-inv", "/dev/null", "-print_out", ":",
                "@mem:11", "-S", "-last", "@mem:11", "-nl_out", "@mem:11"
            ]
        else:
            cmds = [
                gfile, "-ftn_api_fn0", "-last0", "@mem:10", "-inv", "/dev/null"
            ]
        if sequential <= 0:
            cmds.append('-rewind_init')
            cmds.append(gfile)
        if sequential >= 0:
            cmds.append('-end')
        for m in matches:
            cmds.append(match_option)
            cmds.append(m)

    # BOUNDS = common.BOUNDS
    ## how to match
    # bounds = [
              # '-undefine',
              # 'out-box',
              # '{}:{}'.format(BOUNDS['longitude']['min'],
                             # BOUNDS['longitude']['max']),
              # '{}:{}'.format(BOUNDS['latitude']['min'],
                             # BOUNDS['latitude']['max'])
             # ]
    # cmds = cmds + bounds
    
    cmds.append("-no_header")
    
    if var != '':
        cmds.append(match_option)
        cmds.append(':' + var + ':')

    if time0 is not None:
        if time0 < 0:
            return -1
        cmds.append(match_option)
        if time0 <= 9999999999:
            cmds.append(':d=' + str(time0) + ':')
        else:
            cmds.append(':D=' + str(time0) + ':')

    if ftime != '':
        cmds.append(match_option)
        cmds.append(':' + ftime + ':')

    if level != '':
        cmds.append(match_option)
        cmds.append(':' + level + ':')

    if Data != False:
        cmds.append("-rpn")
        cmds.append("sto_13")

    if Latlon != False:
        cmds.append("-rpn")
        cmds.append("rcl_lon:sto_14:rcl_lat:sto_15")
    # logging.debug("Call")
    err = wgrib2(cmds)

    if err > 0:
        if debug: print("inq ",gfile,": wgrib2 failed err=", err)
        nmatch = -1
        return -1

    if mem_size(10) == 0:
        if debug: print("no match")
        nmatch = 0
        return 0

    string = get_str_mem(10)
    x = string.split()
    nmatch = int(x[0])
    ndata = int(x[1])
    nx = int(x[2])
    ny = int(x[3])
    msgno = int(x[4])
    submsgno = int(x[5])
    if (nmatch == 0):
        if debug: print("inq ",gfile," found no matches")
        return 0

# for weird grids nx=-1/0 ny=-1/0
    if (nx * ny != ndata):
        nx = ndata
        ny = 1
    # logging.debug("Load")
# get data, lat/lon
    if (Data != False or Latlon != False):
        array_type = (c_float * ndata)
        array = array_type()

        if (Data != False):
            err = my_wgrib2.wgrib2_get_reg_data(byref(array), ndata, 13)
            if (err == 0):
                data = np.reshape(np.array(array), (nx, ny), order='F')
                if use_np_nan:
                    data[np.logical_and((data > UNDEFINED_LOW), (data < UNDEFINED_HIGH))] = np.nan
        if (Latlon != False):
            err = my_wgrib2.wgrib2_get_reg_data(byref(array), ndata, 14)
            if (err == 0):
                lon = np.reshape(np.array(array), (nx, ny), order='F')
                if use_np_nan:
                    lon[np.logical_and((lon > UNDEFINED_LOW), (lon < UNDEFINED_HIGH))] = np.nan
            err = my_wgrib2.wgrib2_get_reg_data(byref(array), ndata, 15)
            if (err == 0):
                lat = np.reshape(np.array(array), (nx, ny), order='F')
                if use_np_nan:
                    lat[np.logical_and((lat > UNDEFINED_LOW), (lat < UNDEFINED_HIGH))] = np.nan
    # logging.debug("Done")
    if Matched != False:
        size = my_wgrib2.wgrib2_get_mem_buffer_size(11)
        string = create_string_buffer(size)
        err = my_wgrib2.wgrib2_get_mem_buffer(string, size, 11)
        if (err == 0):
            matched = string.value.decode("utf-8").rstrip().split('\n')

    if debug:
        print("inq nmatch=", nmatch)
        print("ndata=", ndata, nx, ny)
        print("msg=", msgno, submsgno)
        print("has_data=", data is not None)
    return nmatch



#####################################################################

def get_data(gfile,
             *matches,
             select='',
             Regex=False):
    # logging.debug("Start")
    # based on grb2_inq() from ftn wgrib2api

    data = None
    lat = None
    lon = None
    matched = []
    match_option = '-fgrep'
    
    if select != '':  # selected field, use -d, sequential not valid
        cmds = [
            gfile, "-d", select, "-ftn_api_fn0", "-last0", "@mem:10",
            "-inv", "/dev/null"
        ]
    else:  # no inventory
        cmds = [
            gfile, "-ftn_api_fn0", "-last0", "@mem:10", "-inv", "/dev/null"
        ]
        cmds.append('-rewind_init')
        cmds.append(gfile)
        for m in matches:
            cmds.append(match_option)
            cmds.append(m)

    cmds.append("-no_header")
    cmds.append("-rpn")
    cmds.append("sto_13")
    err = wgrib2(cmds)

    if err > 0:
        if debug: print("inq ",gfile,": wgrib2 failed err=", err)
        nmatch = -1
        return -1

    if mem_size(10) == 0:
        if debug: print("no match")
        nmatch = 0
        return 0

    string = get_str_mem(10)
    x = string.split()
    nmatch = int(x[0])
    ndata = int(x[1])
    nx = int(x[2])
    ny = int(x[3])
    msgno = int(x[4])
    submsgno = int(x[5])
    if (nmatch == 0):
        if debug: print("inq ",gfile," found no matches")
        return None

# for weird grids nx=-1/0 ny=-1/0
    if (nx * ny != ndata):
        nx = ndata
        ny = 1
    # logging.debug("Load")
# get data, lat/lon
    array_type = (c_float * ndata)
    array = array_type()

    err = my_wgrib2.wgrib2_get_reg_data(byref(array), ndata, 13)
    if (err == 0):
        data = np.reshape(np.array(array), (nx, ny), order='F')
        if use_np_nan:
            data[np.logical_and((data > UNDEFINED_LOW), (data < UNDEFINED_HIGH))] = np.nan
    # logging.debug("Done")

    if debug:
        print("inq nmatch=", nmatch)
        print("ndata=", ndata, nx, ny)
        print("msg=", msgno, submsgno)
        print("has_data=", data is not None)
    return data



#####################################################################

def match(gfile):
    # logging.debug("Start")
    # based on grb2_inq() from ftn wgrib2api

    data = None
    lat = None
    lon = None
    matched = []
    match_option = '-match_fs'
    cmds = [
        gfile, "-last", "@mem:11", "-ftn_api_fn0", "-last0", "@mem:10",
        "-inv", "/dev/null", "-print_out", ":",
        "@mem:11", "-S", "-last", "@mem:11", "-nl_out", "@mem:11"
    ]
    cmds.append('-rewind_init')
    cmds.append(gfile)
    cmds.append("-no_header")
    err = wgrib2(cmds)

    if err > 0:
        if debug: print("inq ",gfile,": wgrib2 failed err=", err)
        nmatch = -1
        return -1

    if mem_size(10) == 0:
        if debug: print("no match")
        nmatch = 0
        return 0

    string = get_str_mem(10)
    x = string.split()
    nmatch = int(x[0])
    ndata = int(x[1])
    nx = int(x[2])
    ny = int(x[3])
    msgno = int(x[4])
    submsgno = int(x[5])
    if (nmatch == 0):
        if debug: print("inq ",gfile," found no matches")
        return 0

# for weird grids nx=-1/0 ny=-1/0
    if (nx * ny != ndata):
        nx = ndata
        ny = 1
    # logging.debug("Load")
    size = my_wgrib2.wgrib2_get_mem_buffer_size(11)
    string = create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, 11)
    if (err == 0):
        matched = string.value.decode("utf-8").rstrip().split('\n')

    if debug:
        print("inq nmatch=", nmatch)
        print("ndata=", ndata, nx, ny)
        print("msg=", msgno, submsgno)
        print("has_data=", data is not None)
    return matched


#####################################################################
fix180 = np.vectorize(lambda x: x if x <= 180 else x - 360)

def coords(gfile):
    # logging.debug("Start")
    # based on grb2_inq() from ftn wgrib2api
    data = None
    lat = None
    lon = None
    matched = []
    match_option = '-match_fs'
    cmds = [
            gfile, "-ftn_api_fn0", "-last0", "@mem:10", "-inv", "/dev/null"
           ]
    cmds.append('-rewind_init')
    cmds.append(gfile)
    cmds.append("-no_header")
    cmds.append("-rpn")
    cmds.append("rcl_lon:sto_14:rcl_lat:sto_15")
    err = wgrib2(cmds)

    if err > 0:
        if debug: print("inq ",gfile,": wgrib2 failed err=", err)
        nmatch = -1
        return -1

    if mem_size(10) == 0:
        if debug: print("no match")
        nmatch = 0
        return 0

    string = get_str_mem(10)
    x = string.split()
    nmatch = int(x[0])
    ndata = int(x[1])
    nx = int(x[2])
    ny = int(x[3])
    msgno = int(x[4])
    submsgno = int(x[5])
    if (nmatch == 0):
        if debug: print("inq ",gfile," found no matches")
        return None

# for weird grids nx=-1/0 ny=-1/0
    if (nx * ny != ndata):
        nx = ndata
        ny = 1
    # logging.debug("Load")
# get data, lat/lon
    array_type = (c_float * ndata)
    array = array_type()

    err = my_wgrib2.wgrib2_get_reg_data(byref(array), ndata, 14)
    if (err == 0):
        lon = np.reshape(np.array(array), (nx, ny), order='F')
        if use_np_nan:
            lon[np.logical_and((lon > UNDEFINED_LOW), (lon < UNDEFINED_HIGH))] = np.nan
    err = my_wgrib2.wgrib2_get_reg_data(byref(array), ndata, 15)
    if (err == 0):
        lat = np.reshape(np.array(array), (nx, ny), order='F')
        if use_np_nan:
            lat[np.logical_and((lat > UNDEFINED_LOW), (lat < UNDEFINED_HIGH))] = np.nan

    if debug:
        print("inq nmatch=", nmatch)
        print("ndata=", ndata, nx, ny)
        print("msg=", msgno, submsgno)
        print("has_data=", data is not None)
    lon = fix180(lon)
    return np.dstack([lat, lon])

#####################################################################


#
# write grib message
#   returns string of metadata (-S)
#   '' for error
#
def write(gfile,
          template,
          msgno,
          new_data=None,
          Append=False,
          var='',
          lev='',
          time0=None,
          ftime='',
          packing='',
          d_scale=None,
          b_scale=None,
          encode_bits=None,
          sec0=None,
          sec1=None,
          sec2=None,
          sec3=None,
          sec4=None,
          sec5=None,
          sec6=None,
          sec7=None,
          sec8=None,
          pdt=None,
          metadata=''):
    #
    # write grib message (record)
    #
    global use_np_nan, UNDEFINED, debug

#   if you only change metadata, no need to pack grid point data
    pack = False

    cmds = [
        template, "-rewind_init", template, "-d",
        str(msgno), "-inv", "@mem:11", "-no_header"
    ]

    for sec, value in enumerate([sec0, sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8]):
        if value is not None:
            if isinstance(value,bytes) or (isinstance(value[0],bytes) and len(value[0]) == 1):
                size = c_int(len(value))
                err = my_wgrib2.wgrib2_set_mem_buffer(value, size, sec+16)
            else:
                print("sec",sec," type not handled", type(value))
                quit(1)
            if debug == True: print("writing sec",sec)
            cmds.append("-rewind_init")
            cmds.append("@mem:"+str(sec+16))
            cmds.append("-read_sec")
            cmds.append(str(sec))
            cmds.append("@mem:"+str(sec+16))

    if pdt is not None:
        cmds.append("-set_pdt")
        cmds.append("+"+str(pdt))

    # metadata is first source, var, lev are applied afterwards
    if metadata != '':
        cmds.append("-set_metadata_str")
        cmds.append(metadata)

    if time0 is not None:
        cmds.append("-set_date")
        cmds.append(str(time0))

    if var != '':
        cmds.append("-set_var")
        cmds.append(var)

    if lev != '':
        cmds.append("-set_lev")
        cmds.append(lev)

    if ftime != '':
        cmds.append("-set_ftime")
        cmds.append(ftime)

    if packing != '':
        cmds.append("-set_grib_type")
        cmds.append(packing)
        pack = True

    # set grid point data
    # -rpn will clear scaling parameters, so set grid point data first
    
    if new_data is not None:
        asize = new_data.size
        a = new_data.astype(dtype=np.float32).reshape((asize),order='F')
        if use_np_nan:
            a[np.isnan(a)] = UNDEFINED
        a_p = a.ctypes.data_as(c_void_p)
        err = my_wgrib2.wgrib2_set_reg(a_p, asize, 10)
        cmds.append("-rpn")
        cmds.append("rcl_10")
        pack = True

    if d_scale == "same" or b_scale == "same":
        cmds.append("-set_grib_max_bits")
        cmds.append("24")
        cmds.append("-set_scaling")
        cmds.append("same")
        cmds.append("same")
        pack = True
    elif d_scale is not None or b_scale is not None:
        if d_scale is None:
            d_scale = 0
        if b_scale is None:
            b_scale = 0
        cmds.append("-set_grib_max_bits")
        cmds.append("24")
        cmds.append("-set_scaling")
        cmds.append(str(d_scale))
        cmds.append(str(b_scale))
        pack = True

    if encode_bits is not None:
        cmds.append("-set_grib_max_bits")
        cmds.append("24")
        cmds.append("-set_bin_prec")
        cmds.append(str(encode_bits))
        pack = True

#     Write out grib message

    if Append != False:
        cmds.append("-append")
    if pack == False:
        cmds.append("-grib")
    else:
        cmds.append("-grib_out")
    cmds.append(gfile)
    cmds.append("-S")

    err = wgrib2(cmds)
    if err != 0:
        if debug: print("write: wgrib2 err=", err)
        return None
    size = my_wgrib2.wgrib2_get_mem_buffer_size(11)
    string = create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, 11)
    if (err != 0):
        if debug: print("write: err=", err)
        return None
    else:
        return string.value.decode("utf-8").rstrip()


def read_inv(file):
    #
    # read inventory from memory or regular file
    # returns the inventory as a list
    #
    global debug
    if file[0:5] == '@mem:':
        i = int(file[5:])
        a = get_str_mem(i)
    else:
        close(file)
        f = open(file, 'r')
        a = f.read()
        f.close()

    if a == '':
        return []
    s = a.rstrip().split('\n')
    return s

#
# get the version of wgrib2 and configuration functions
#

def wgrib2_version():
    err = wgrib2(['-inv', '@mem:10','-version'])
    size = my_wgrib2.wgrib2_get_mem_buffer_size(10)
    string = create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, 10)
    s = string.value.decode("utf-8")
    return s

def wgrib2_config():
    err = wgrib2(['-inv', '@mem:10','-config'])
    size = my_wgrib2.wgrib2_get_mem_buffer_size(10)
    string = create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, 10)
    s = string.value.decode("utf-8")
    s = s.rstrip().split('\n')
    return s

#
# These are low level api functions
#


def mem_size(arg):
    #
    #     return size of @mem:arg
    #
    global debug
    i = c_int(arg)
    size = my_wgrib2.wgrib2_get_mem_buffer_size(i)
    if debug: print("mem_buffer ",arg," size=", size)
    return size


def get_str_mem(arg):
    #
    #    return a string of contents of @mem:arg
    #
    global debug
    i = c_int(arg)
    size = my_wgrib2.wgrib2_get_mem_buffer_size(i)
    string = create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, i)
    if debug: print("get_str_mem ",arg," err=", err)
    s = string.value.decode("utf-8")
    return s

def get_bytes_mem(arg):
    #
    #    return bytes with contents of @mem:arg
    #
    global debug
    i = c_int(arg)
    size = my_wgrib2.wgrib2_get_mem_buffer_size(i)
    if debug: print("get_bytes_mem: size=",size)
    array = create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(array, size, i)
    if debug: print("get_byte_mem ", arg," err=", err)
    return array

def get_flt_mem(mem_no):
    # return contents of mem file as np array (vector)
    global debug
    i = c_int(mem_no)
    size = my_wgrib2.wgrib2_get_mem_buffer_size(i)
    if (size % 4) != 0:
        if debug: print("*** ERROR: get_flt_mem, not float @mem",mem_no)
        return None
    size_flt = int(size / 4)
    array_type = (c_float * size_flt)
    array = array_type()
    err = my_wgrib2.wgrib2_get_mem_buffer(byref(array), size, i)
    if err != 0:
        if debug: print("*** ERROR: get_flt_mem, could not read @mem",mem_no)
        return None
    data = np.array(array)
    if use_np_nan:
        data[np.logical_and((data > UNDEFINED_LOW), (data < UNDEFINED_HIGH))] = np.nan
    if debug: print("get_flt_mem ", arg)
    return data


def set_mem(mem_no,data):
    global debug, use_np_nan
    i = c_int(mem_no)

    # data can be type bytes, str or something else in future
    if isinstance(data,bytes) or (isinstance(data[0],bytes) and len(data[0]) == 1):
        size = c_int(len(data))
        err = my_wgrib2.wgrib2_set_mem_buffer(data, size, i)
    elif isinstance(data[0],bytes):
        # array of 1 character
        size = c_int(len(data))
        err = my_wgrib2.wgrib2_set_mem_buffer(data, size, i)
    elif isinstance(data, str):
        size = c_int(len(data))
        a = data.encode('utf-8')
        err = my_wgrib2.wgrib2_set_mem_buffer(a, size, i)
    elif isinstance(data, np.ndarray):
        asize = data.size
        size = c_int(4*asize)
        a = data.astype(dtype=np.float32).reshape(asize)
        if use_np_nan:
            a[np.isnan(a)] = UNDEFINED
        a_p = a.ctypes.data_as(c_void_p)
        err = my_wgrib2.wgrib2_set_mem_buffer(a_p, size, i)
    else:
        print("set_mem does not support ",type(data))
        err = 1
    if (debug): print("set_mem ",mem_no," err=", err)
    return err

#
#  register routines
#

def reg_size(regno):
    # return size of register-arg
    global debug
    i = c_int(regno)
    size = my_wgrib2.wgrib2_get_reg_size(i)
    if debug: print("reg ",regno," size=",size)
    return size

def get_reg(regno):
    # return register(arg) as np array (vector)
    #
    # get size of register
    #
    global use_np_nan, debug
    i = c_int(regno)
    size = my_wgrib2.wgrib2_get_reg_size(i)
    array_type = (c_float * size)
    array = array_type()
    err = my_wgrib2.wgrib2_get_reg_data(byref(array), size, i)
    if err != 0:
       if debug: print("wgrib2_get_reg reg",i," err=", err)
       return None
    # don't know dimensions of register
    data = np.array(array)
    if use_np_nan:
        data[np.logical_and((data > UNDEFINED_LOW), (data < UNDEFINED_HIGH))] = np.nan
    if debug: print("get_reg ",regno)
    return data

def set_reg(regno, array):
    #
    # set register(regno) = array
    #
    global use_np_nan, debug
    i = c_int(regno)
    if debug:
        print("set_reg ",i)
    asize = array.size

    # convert array to 32-bit float, linear
    a = array.astype(dtype=np.float32).reshape((asize))
    if use_np_nan:
        a[np.isnan(a)] = UNDEFINED
    a_p = a.ctypes.data_as(c_void_p)

    err = my_wgrib2.wgrib2_set_reg(a_p, asize, i)
    if debug: print("set_reg ",i," err=", err)
    return err
