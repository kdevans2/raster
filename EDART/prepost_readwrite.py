# -*- coding: utf-8 -*-
"""
---------------------------------------------------------------------------
 prepost_readwrite.py
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
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# recording functions
def blank_line(sROIID_, sComment_, iIndexCount_):
    """ Return correctly sized filler line for when extract is not possible. """
    iCommaCount = 2 * iIndexCount_ + 1
    return f'"{sROIID_}"{"," * iCommaCount}{sComment_}'

def write_blank(sROIID_, sComment_, txt_, iIndexCount=4):
    """ Write blank record to txt. """
    print(f'\t{sComment_}, skipping')
    sBlank = blank_line(sROIID_, sComment_, iIndexCount)
    txt_.write(f'{sBlank}\n')

def write_record(sROIID_, aM, txt_, sComment_='', sComment2_='', sComment3_=''):
    """ Write record to txt. """
    sM = ','.join(f'{aM[0,i]},{aM[1,i]}' for i in range(aM.shape[1]))
    sRec = f'"{sROIID_}",{sM},{sComment_},{sComment2_},{sComment3_}'
    txt_.write(f'{sRec}\n')

# ---------------------------------------------------------------------------
# pandas recording functions
def appendSeries(sr_, df_, sComment='', sCommentCol='comment'):
    """ Return dataframe df_ with series sr_ appended
        sr_.sCommentCol = sComment prior to append.
    """
    sr_[sCommentCol] = sComment
    return df_.append(sr_, ignore_index=True)

# ---------------------------------------------------------------------------
# read text functions
def read_datetext(sPathTxt_):
    """ Return date array from text file sPathTxt. """
    lstD = [datetime.date(*[int(s) for s in l.strip().split('.')]) for l in open(sPathTxt_, 'r').readlines()]
    return np.array(lstD)

def read_ROIID_texts(lPathTxt_, tF=('Index', 'Mask')):
    """ Return index and mask arrays from text file sPathTxt. """
    lDF = [pd.read_csv(t) for t in lPathTxt_]
    aIndex_ = np.stack([np.array(df[tF[0]]) for df in lDF]).transpose()
    aMask_ = np.array(lDF[0][tF[1]])

    return aIndex_, aMask_

def ROIID_txt_name(sROIID, BANDNAME_, sSubDir=None):
    """ Return ROIID text name. """
    if sSubDir:
        return f'{sSubDir}/{BANDNAME_}/{BANDNAME_}__{sROIID}.txt'
    return f'{BANDNAME_}/{BANDNAME_}__{sROIID}.txt'
