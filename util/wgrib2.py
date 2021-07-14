#  pywgrib2 5/2020 public domain Wesley Ebisuzaki
#
# provides a simple python interface for reading/writing grib for python based 
# on the fortran wgrib2api
#
#   requirements: python 3.6, numpy (common but not standard), 
#     ctypes and os.path from the standard library

import ctypes
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
lib = os.path.join(dir,'libwgrib2.so')

try:
    my_wgrib2 = ctypes.CDLL(lib)
except Exception as e:
    print("*** Problem ",e)
    print("*** Will load wgrib2 library in RTLD_LAZY mode")
    my_wgrib2 = ctypes.CDLL(lib, mode=os.RTLD_LAZY)

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
    # print("wgrib2")
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

#####################################################################

def get_all_data(mask,
                 indices,
                 matches,
                 Regex=False):
    # logging.debug("Start")
    # based on grb2_inq() from ftn wgrib2api

    data = None
    lat = None
    lon = None
    matched = []
    match_option = '-fgrep'
    
    cmds = [
        'XXXX', "-d", 'XXXX', "-ftn_api_fn0", "-last0", "@mem:10",
        "-inv", "/dev/null"
    ]

    cmds.append("-no_header")
    cmds.append("-rpn")
    cmds.append("sto_13")
    def do_get(gfile, select):
        cmds[0] = gfile
        # logging.debug(select)
        cmds[2] = select
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
        return data
    results = {}
    for i in range(len(indices)):
        m = indices[i]
        gfile = mask.format(m)
        logging.debug(m)
        results[m] = []
        for select in matches:
            results[m].append(do_get(gfile, select))
    # results = list(map(do_get, matches))
    return results

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
