"""
---------------------------------------------------------------------------
 EDARTUtility.py
 09/2018

 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 Script to: EDART post processing support functions.
 Many of these functions could in theory be moved to a more generic
    raster module, but all should be assumed to make assumptions specific
    to EDART outputs.

 V1. changes to working dir functions. remove support for older working dir methods

 Known limitations: python 3.x
---------------------------------------------------------------------------
"""
import os
import glob
import shutil
import sys
import time
import calendar
import numpy as np
import arcpy
sys.path.append(os.path.abspath(r'..'))
import envi_header

# ------------------------------
# event timing raster (EVTY)
EVENTSUFFIX = 'EVTY'
# corresponding confidence raster (ConfEV)
CONFSUFFIX = 'ConfEV'
# low confidence suffix
EVENTXSUFFIX = 'EVpTY'
# event frame raster
FRAMEEVENTSUFFIX = 'nFrEV'
# prepost stat raster
PPSUFFIX = 'PPEVdif'

# ---------------------------------------------------------------------------
# numpy related and for pool
def testYear(a, intY, intYEnd=None):
    """ Return 1 where intY <= a < intYEnd, else 0.
        Works 2 and 3D.
    """
    if intYEnd is None:
        intYEnd = intY + 1
    return (np.where(a >= intY, 1, 0) & np.where(a < intYEnd, 1, 0)).astype(np.uint8)

def testMoistureYear(a, intY):
    """ Return 1 where intY < a >= intY else 0.
        Works 2 and 3D.
        Currently hardcoded for Oct 1 start date:
            intY = 2000 --> from Oct1 2000 thru sept30 2001
    """
    intD = 274
    intDL = 275
    # set start and end
    fltY = intY + intD/365
    fltYEnd = intY + 1 + intD/365
    # Check for leap year start and end
    if calendar.isleap(intY):
        fltY = intY + intDL/366
    if calendar.isleap(intY + 1):
        fltYEnd = intY + 1 + intDL/366

    return testYear(a, fltY, fltYEnd)

# ---------------------------------------------------------------------------
# path and file related
def getSceneDir(strPathTDIS):
    """ Return scene folder given TDIS folder. """
    if not r'envi_aux\TDIS' in strPathTDIS:
        raise Exception(r'pattern match "envi_aux\TDIS" not found.')
    return strPathTDIS.split(r'envi_aux\TDIS')[0]

def getDMDir(strPathScene):
    """ Return directory containing cloud masks
        mask bsqs in this dir are named DM_yyyy.mm.dd_X.bsq
    """
    return strPathScene + r'envi_aux\Images'

def getDartDir(strPathScene):
    """ Return directory containing 
    """
    strWild = strPathScene + r'envi_aux\Images\DF_*'
    lstDirs = [f for f in glob.glob(strWild) if os.path.isdir(f)]

    if len(lstDirs) == 0:
        raise Exception('No match found for: ' + strWild)
    elif len(lstDirs) > 1:
        raise Exception('Multiple matchs found for: ' + strWild)

    return lstDirs[0]

def getENVIframeDir(strPathScene, sSubDir=None):
    """ Return directory containing envi frames
        frame bsqs in this dir are named FR_yyyy.mm.dd_X.bsq
        Optional subdirectory name sSubDir. workaround for non standard directory organization.
    """
    strWild = strPathScene + r'SEQhdr\ENVI_FR*'
    if sSubDir is not None:
        strWild = strWild + os.sep + sSubDir

    lstDirs = [f for f in glob.glob(strWild) if os.path.isdir(f)]

    if len(lstDirs) == 0:
        raise Exception('No match found for: ' + strWild)
    elif len(lstDirs) > 1:
        raise Exception('Multiple matchs found for: ' + strWild)

    return lstDirs[0]

def get_workspace(strOrigPath, strType_='flatten', strSuff_=''):
    """ Return TDIS working (flatten) path given TDIS path. """
    if os.path.split(strOrigPath)[1].startswith('TDISm__'):
        strScene = strOrigPath.split(os.sep)[-4].split('_')[0]
        p, f = os.path.split(strOrigPath)
        strWorkPath = p + os.sep + strScene + '_' + f + '_' + strType_ + strSuff_
    else:
        print('Archive style folder name.')
        strWorkPath = strOrigPath + '_flatten'

    return strWorkPath

def expand2TDISpath(strPath):
    """ Return full TDIS working folder (.../envi_aux/TDIS/TDISm__*) given only scene folder.
        Raise exception if zero or more than one match is found.
    """
    if 'TDISm__' in os.path.split(strPath)[1]:
        return strPath

    strWild = strPath + r'\envi_aux\TDIS\TDISm__*'
    lstDirs = glob.glob(strWild)
    if len(lstDirs) == 0:
        raise Exception('No match found for: ' + strWild)
    elif len(lstDirs) > 1:
        raise Exception('Multiple matchs found for: ' + strWild)

    return lstDirs[0]

def prep_workspace(strOriginalPath, strType_, strSuff_='', bolRedo_=False):
    """ Determine and create workspace folder
        Options:
            bolRedo_: Delete existing working folder and redo.
    """
    print('\tPrep...')
    strWorkingPath = get_workspace(strOriginalPath, strType_=strType_, strSuff_=strSuff_)
    print('\t\tWorking path: ' + strWorkingPath)
    if os.path.exists(strWorkingPath):
        if bolRedo_:
            print('\t\tRemoving old run.')
            shutil.rmtree(strWorkingPath)
            time.sleep(2)
            os.makedirs(strWorkingPath)
        else:
            return None
    else:
        os.makedirs(strWorkingPath)

    return strWorkingPath

def ImgHdrPair(strPathImg, strExt='.hdr'):
    """ Return raster and header path given raster. """
    return (strPathImg, strPathImg[:-4] + strExt)

def CopyBsq(lstBsq, strOutPath):
    """ Copy all bsqs in lstBsq to strOutPath.
        Optionally copy to os.cwd if strOutPath is None
    """
    lstCopied = []
    for inB in lstBsq:
        inB, inH = ImgHdrPair(inB)
        outB, outH = [strOutPath + os.sep + os.path.basename(f) for f in [inB, inH]]
        shutil.copy(inB, outB)
        shutil.copy(inH, outH)

        lstCopied.append(outB)

    return lstCopied

def get_PPEVdif(strPath, strBand_, strStat_='Median'):
    """ Return FrEV raster name given TDIS path.
        Should combine with below functions
    """
    lstSearch = glob.glob(strPath + os.sep + PPSUFFIX + '_' + strStat_ + '_' + strBand_ + '*.tif')
    if len(lstSearch) != 1:
        raise Exception('Non-unique or missing propost stat image: ' + str(lstSearch))
    return lstSearch[0]

def get_nFrEV(strPath):
    """ Return FrEV raster name given TDIS path.
        Should combine with below functions
    """
    lstSearch = glob.glob(strPath + os.sep + FRAMEEVENTSUFFIX + '_*.bsq')
    if len(lstSearch) != 1:
        raise Exception('Non-unique or missing nFrEV image: ' + str(lstSearch))
    return lstSearch[0]

def get_EVTY(strPath):
    """ Return EVTY raster name given TDIS path. """
    lstSearch = glob.glob(strPath + os.sep + EVENTSUFFIX + '_*.bsq')
    if len(lstSearch) != 1:
        raise Exception('Non-unique or missing event timing image: ' + str(lstSearch))
    return lstSearch[0]

def get_ConfEV(strPath):
    """ Return ConfEVTY raster name given TDIS path. """
    lstSearch = glob.glob(strPath + os.sep + CONFSUFFIX + '_*.bsq')
    if len(lstSearch) != 1:
        raise Exception('Non-unique or missing event confidence image: ' + str(lstSearch))
    return lstSearch[0]

def IngestFramesPartial(strPathScene_, BANDNAME_, tupShp, lRawDates=None, bReturnDateLU=False):
    """ Return ND array of DF frames.
        No cloud masking done.
        No transform or change of arr dtype
    """
    strDartPath = getDartDir(strPathScene_)
    strFramesPath = getENVIframeDir(strPathScene_, sSubDir='all_frames')
    strMasksPath = getDMDir(strPathScene_)

    print('\tIngest and mask frames...')
    if lRawDates is None:
        print('\tResiduals...')
        lstFrames = glob.glob(strDartPath + r'/DF_*.bsq')
        lstFrames.sort()
    else:
        print('\tRaw...')
        lstFrames = glob.glob(strFramesPath + r'/FR_*.bsq')
        lstFrames = [f for f in lstFrames if getDate_nF(f)[0] in lRawDates]
        lstFrames.sort()

    # intialize target
    # note: arr3D_Index is NOT initiallized with an extra band [0,:,:] as in IngestFrames.
    nrow, ncol = tupShp
    arr3D_Index_ = np.zeros((len(lstFrames), nrow, ncol), dtype=np.int16)
    arr3D_Mask_ = np.zeros((len(lstFrames), nrow, ncol), dtype=np.int16)
    dicLU = {}
    dicLUdate = {}
    print('\t\tZeros: ', arr3D_Index_.shape)
    for i, fr in enumerate(lstFrames):
        iHDR = envi_header.HDR(fr)
        strBand = iHDR.bandName_wild(BANDNAME_)
        strPathFR = fr + os.sep + strBand
        strDate, strnF = getDate_nF(fr)
        strPathDM = strMasksPath + r'/DM_' + strDate + '_' + strnF + '.bsq'

        print('\t\t' + strBand)
        arr3D_Index_[i, :, :] = arcpy.RasterToNumPyArray(strPathFR, ncols=ncol, nrows=nrow)
        arr3D_Mask_[i, :, :] = arcpy.RasterToNumPyArray(strPathDM, ncols=ncol, nrows=nrow)
        dicLU[int(strnF)] = i
        dicLUdate[i] = strDate

    if bReturnDateLU:
        return arr3D_Index_, arr3D_Mask_, dicLU, dicLUdate

    return arr3D_Index_, arr3D_Mask_, dicLU

def getDate_nF(r):
    """ Return date and frame number given raster name.
        Works for DM, DF and FR bsqs.
    """
    return os.path.splitext(os.path.basename(r))[0].split('_')[1:3]

if __name__ == "__main__":
    pass
