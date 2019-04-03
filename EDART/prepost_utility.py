# -*- coding: utf-8 -*-
"""
---------------------------------------------------------------------------
 prepost_utility.py
 02/2019

 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 script to:

 Known limitations: python 3.6
---------------------------------------------------------------------------
"""
import datetime
import math
import numpy as np

# ---------------------------------------------------------------------------
# rga transform
def transform_rga(fRGA):
    """ Return inverse transform of dRGA values.
        RGA assummed to be in degrees, not radians!
        Note RGA rasters are writen scaled, see scale RGA.
    """
    return math.tan(math.pi* fRGA / 180)

def descale_rga(fRGA, fScale=100):
    """ de-scale dRGA values.
        RGA rasters are writen scaled, i.e. RGAscaled = RGA * fScale
    """
    return fRGA / fScale

def descale_transform_rga(fRGA):
    """ Combine transform_rga and  descale_rga. """
    return transform_rga(descale_rga(fRGA))

def add_transformed_rga(dfIn, lColumn_, lColumnT_):
    """ Add tranform of fields in lColumn as fields in lColumnT. """
    for sColumn, sColumnT in zip(lColumn_, lColumnT_):
        dfIn[sColumnT] = dfIn[sColumn].apply(descale_transform_rga)
    return dfIn

# ---------------------------------------------------------------------------
# time filtering
def split_pre(aI_, aD_, d_, iDays=548):
    """ Return aI_, aM_, aD_  masked to within 1.5 years (or iDays).
        Pre arrays are returned reversed (starting with date closest to d0)
    """
    aTest = np.logical_and(aD_ < d_, aD_ > d_ - datetime.timedelta(iDays))
    aIpre = aI_[aTest]
    aDpre = aD_[aTest]

    return np.flip(aIpre, axis=0), np.flip(aDpre, axis=0)

def split_post(aI_, aD_, d_, iDays=548):
    """ Return aI_, aM_, aD_  masked to within 1.5 years (or iDays). """
    aTest = np.logical_and(aD_ > d_, aD_ < d_ + datetime.timedelta(iDays))
    aIpost = aI_[aTest]
    aDpost = aD_[aTest]

    return aIpost, aDpost

def timestamp_to_date(ts):
    """ Return datetime date from pandas timestamp. """
    return datetime.date(ts.year, ts.month, ts.day)

def isMonth(d_):
    """ Return true if date is August thru September. """
    tMonths_ = (8, 9)
    return d_.month in tMonths_

isMonthV = np.vectorize(isMonth)

# ---------------------------------------------------------------------------
# other filtering

def drop_masked(aI_, aM_, aD_):
    """ Return aI_, aD_ with masked DM values removed. """
    aKeep = np.logical_or(aM_ == 0, aM_ >= 200)
    return aI_[aKeep], aD_[aKeep]

def drop_zeros(aI_, aD_, tDropZerosSlice_=None):
    """ Return aI_, aD_ with all 0 ([0,0,0,0]) frames (axis=1 in aI_) removed.
        Optional iWidth: do zeros check only over first iWidth columns.
            (meant to separate z2 columns from raw columns)
    """
    if tDropZerosSlice_ is None:
        iStart, iEnd = 0, aI_.shape[1]
    else:
        iStart, iEnd = tDropZerosSlice_

    aKeep = ~np.logical_and(np.ptp(aI_[:, iStart:iEnd], axis=1) == 0,
                            np.sum(aI_[:, iStart:iEnd], axis=1) == 0)
    return aI_[aKeep], aD_[aKeep]
