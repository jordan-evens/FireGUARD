# this file is adapted from:
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

# libwgrib2.so must be in same dir as this file, can be link to file
import site
dir=site.getsitepackages()[0]
lib = os.path.join(dir,'libwgrib2.so')
stdlib = ctypes.CDLL("")
dll_close = stdlib.dlclose
dll_close.argtypes = [ctypes.c_void_p]

def open():
    try:
        my_wgrib2 = ctypes.CDLL(lib)
    except Exception as e:
        logging.warning("*** Problem ",e)
        logging.warning("*** Will load wgrib2 library in RTLD_LAZY mode")
        my_wgrib2 = ctypes.CDLL(lib, mode=os.RTLD_LAZY)
    return my_wgrib2

def close(my_wgrib2):
    dll_close(my_wgrib2._handle)
    del my_wgrib2

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

def wgrib2(my_wgrib2, arg):
    #
    #    call wgrib2
    #        ex.  pywgrib2.wgrib2(["in.grb","-inv","@mem.0"])
    #
    #    uses C calling convention: 1st arg is name of program
    #
    # logging.debug("wgrib2")
    arg_length = len(arg) + 3
    select_type = (ctypes.c_char_p * arg_length)
    select = select_type()
    item = "pywgrib2"
    select[0] = item.encode('utf-8')
    item = "-names"
    select[1] = item.encode('utf-8')
    select[2] = names.encode('utf-8')
    
    for key, item in enumerate(arg):
        select[key + 3] = item.encode('utf-8')

    if debug: logging.debug("wgrib2 args: ", arg)
    err = my_wgrib2.wgrib2(arg_length, select)
    if debug: logging.debug("wgrib2 err=", err)
    return err

#####################################################################

def get_all_data(my_wgrib2,
                 mask,
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
        err = wgrib2(my_wgrib2, cmds)

        if err > 0:
            if debug: logging.error("inq ",gfile,": wgrib2 failed err=", err)
            nmatch = -1
            return -1

        if mem_size(my_wgrib2, 10) == 0:
            if debug: logging.warning("no match")
            nmatch = 0
            return 0

        string = get_str_mem(my_wgrib2, 10)
        x = string.split()
        nmatch = int(x[0])
        ndata = int(x[1])
        nx = int(x[2])
        ny = int(x[3])
        msgno = int(x[4])
        submsgno = int(x[5])
        if (nmatch == 0):
            if debug: logging.warning("inq ",gfile," found no matches")
            return None

    # for weird grids nx=-1/0 ny=-1/0
        if (nx * ny != ndata):
            nx = ndata
            ny = 1
        # logging.debug("Load")
    # get data, lat/lon
        array_type = (ctypes.c_float * ndata)
        array = array_type()

        err = my_wgrib2.wgrib2_get_reg_data(ctypes.byref(array), ndata, 13)
        if (err == 0):
            data = np.reshape(np.array(array), (nx, ny), order='F')
            if use_np_nan:
                data[np.logical_and((data > UNDEFINED_LOW), (data < UNDEFINED_HIGH))] = np.nan
        # logging.debug("Done")
        return data
    if debug: logging.info(mask)
    results = {}
    for i in range(len(indices)):
        m = indices[i]
        gfile = mask.format(m)
        if debug: logging.debug(gfile)
        results[m] = []
        for select in matches:
            results[m].append(do_get(gfile, select))
    # results = list(map(do_get, matches))
    return results

#####################################################################

def match(my_wgrib2, gfile):
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
    err = wgrib2(my_wgrib2, cmds)

    if err > 0:
        if debug: logging.error("inq ",gfile,": wgrib2 failed err=", err)
        nmatch = -1
        return -1

    if mem_size(my_wgrib2, 10) == 0:
        if debug: logging.warning("no match")
        nmatch = 0
        return 0

    string = get_str_mem(my_wgrib2, 10)
    x = string.split()
    nmatch = int(x[0])
    ndata = int(x[1])
    nx = int(x[2])
    ny = int(x[3])
    msgno = int(x[4])
    submsgno = int(x[5])
    if (nmatch == 0):
        if debug: logging.warning("inq ",gfile," found no matches")
        return 0

# for weird grids nx=-1/0 ny=-1/0
    if (nx * ny != ndata):
        nx = ndata
        ny = 1
    # logging.debug("Load")
    size = my_wgrib2.wgrib2_get_mem_buffer_size(11)
    string = ctypes.create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, 11)
    if (err == 0):
        matched = string.value.decode("utf-8").rstrip().split('\n')

    if debug:
        logging.debug("inq nmatch=", nmatch)
        logging.debug("ndata=", ndata, nx, ny)
        logging.debug("msg=", msgno, submsgno)
        logging.debug("has_data=", data is not None)
    return matched

#####################################################################
fix180 = np.vectorize(lambda x: x if x <= 180 else x - 360)

def coords(my_wgrib2, gfile):
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
    err = wgrib2(my_wgrib2, cmds)

    if err > 0:
        if debug: logging.error("inq ",gfile,": wgrib2 failed err=", err)
        nmatch = -1
        return -1

    if mem_size(my_wgrib2, 10) == 0:
        if debug: logging.warning("no match")
        nmatch = 0
        return 0

    string = get_str_mem(my_wgrib2, 10)
    x = string.split()
    nmatch = int(x[0])
    ndata = int(x[1])
    nx = int(x[2])
    ny = int(x[3])
    msgno = int(x[4])
    submsgno = int(x[5])
    if (nmatch == 0):
        if debug: logging.warning("inq ",gfile," found no matches")
        return None

# for weird grids nx=-1/0 ny=-1/0
    if (nx * ny != ndata):
        nx = ndata
        ny = 1
    # logging.debug("Load")
# get data, lat/lon
    array_type = (ctypes.c_float * ndata)
    array = array_type()

    err = my_wgrib2.wgrib2_get_reg_data(ctypes.byref(array), ndata, 14)
    if (err == 0):
        lon = np.reshape(np.array(array), (nx, ny), order='F')
        if use_np_nan:
            lon[np.logical_and((lon > UNDEFINED_LOW), (lon < UNDEFINED_HIGH))] = np.nan
    err = my_wgrib2.wgrib2_get_reg_data(ctypes.byref(array), ndata, 15)
    if (err == 0):
        lat = np.reshape(np.array(array), (nx, ny), order='F')
        if use_np_nan:
            lat[np.logical_and((lat > UNDEFINED_LOW), (lat < UNDEFINED_HIGH))] = np.nan

    if debug:
        logging.debug("inq nmatch=", nmatch)
        logging.debug("ndata=", ndata, nx, ny)
        logging.debug("msg=", msgno, submsgno)
        logging.debug("has_data=", data is not None)
    lon = fix180(lon)
    return np.dstack([lat, lon])

#####################################################################

#
# These are low level api functions
#


def mem_size(my_wgrib2, arg):
    #
    #     return size of @mem:arg
    #
    global debug
    i = ctypes.c_int(arg)
    size = my_wgrib2.wgrib2_get_mem_buffer_size(i)
    if debug: logging.debug("mem_buffer ",arg," size=", size)
    return size


def get_str_mem(my_wgrib2, arg):
    #
    #    return a string of contents of @mem:arg
    #
    global debug
    i = ctypes.c_int(arg)
    size = my_wgrib2.wgrib2_get_mem_buffer_size(i)
    string = ctypes.create_string_buffer(size)
    err = my_wgrib2.wgrib2_get_mem_buffer(string, size, i)
    if debug: logging.debug("get_str_mem ",arg," err=", err)
    s = string.value.decode("utf-8")
    return s
