"""
---------------------------------------------------------------------------
combine.py
 Kirk D Evans 07/2018 kdevans@fs.fed.us
    TetraTech EC for:
    USDA Forest Service
    Region 5 Remote Sensing Lab
    
 script to: function NumpyCombine implementing Spatial Analyst Combine.

 known limitations: python 3.x (sort of)
---------------------------------------------------------------------------
"""
import traceback
import time
import sys
import os
import numpy as np
import arcpy
import py3_general.generalARC as gArc
import raster.rasterARCUtility as rastArcU

def uniqueDict(*a):
    ''' '''
    setABC = set(zip(*a))
    dLU = {t:i+1 for i, t in enumerate(setABC)}
    del setABC
    return dLU

def RemoveNoDataKeys(d, NoDataVal):
    ''' Return d with all keys containing NoDataVal removed. '''
    return {k:v for k, v in d.items() if NoDataVal not in k}

def AlterNoDataKeys(d, NoDataVal):
    ''' Return d with all keys containing NoDataVal altered to the NoData value.
        This version (compared to RemoveNoDataKeys) doesn't require the use
        of dict.get method (in WriteLU2)
    '''
    return {k:d.get(k, NoDataVal) for k in d.keys()}
    
def WriteLU(dLU, *a):
    ''' '''
    return np.array([dLU[T] for T in zip(*a)])

def WriteLU2(dLU, NoData, *a):
    ''' '''
    return np.array([dLU.get(T, NoData) for T in zip(*a)])

def NumpyCombine(lstRastersIn, strPathOut, NoDataVal = None):
    ''' Numpy based implementation of Spatial Analyst Combine.
        Limitations: all inputs must match in projection, extent and cell size.
        Function is 2-3 time slower when run in python 2.x
    '''
    # Get description for later writing
    iDesc = gArc.getSimpleDesc(lstRastersIn[0])
    intLength = iDesc.width * iDesc.height
    npType = np.uint16

    print('KirkCombine message: Ingest to 1D...')
    t0 = time.time()
    lstArr = [arcpy.RasterToNumPyArray(strR, nodata_to_value = 0).reshape((1,intLength))[0,:] for strR in lstRastersIn]
    print('\t' + str(time.time() - t0))

    print('KirkCombine message: UniqueVals 2 dictionary...')
    t1 = time.time()
    dicLU = uniqueDict(*lstArr)
    dicLUc = RemoveNoDataKeys(dicLU, NoDataVal)
    print('\t' + str(time.time() - t1))

    # set bit depth based on number of values in dictionary
    #print(len(dicLUc))
    if len(dicLUc) < 255:
        npType = np.uint8
    elif len(dicLUc) < 65534:
        npType = np.uint16
    else:
        npType = np.int32

    print(npType)
    
    print('KirkCombine message: Lookup2...')
    t2 = time.time()
    arrC2c = WriteLU2(dicLUc, NoDataVal, *lstArr)
    print('\t' + str(time.time() - t2))
    
    arrC_2D = arrC2c.reshape(iDesc.shape).astype(npType)

    print('KirkCombine message: ArrayToRaster...')
    #print('Save...')
    t3 = time.time()
    rastArcU.ArrayToRaster(arrC_2D, strPathOut, iDesc, NoDataVal)

    del arrC_2D, arrC2c, lstArr
    #return strPathOut
    

if __name__ == '__main__':
    # testing
    arcpy.env.workspace = r'B:\LiDAR\temp\combine\py2'
    strPathOut = 'combine_4band_int32_dat.tif'
    #strPathOut = r'N:\project\fastemap\DrastTile\Intermediate\testus.tif'

    strInPath = r'B:\LiDAR\temp\combine\KirkComInput'
    
    lstIn = [strInPath + os.sep + 'Combin' + str (i)+ '.tif' for i in range(4)]
    t = time.time()
    #NumpyCombine(lstIn, strPathOut, 0)
    print('Done.\n\t' + str(time.time() - t))
