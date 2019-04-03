"""
---------------------------------------------------------------------------
rasterGDALUtility.py
Kirk D Evans 07/2018 kdevans@fs.fed.us
    TetraTech EC for:
    USDA Forest Service
    Region 5 Remote Sensing Lab

Raster functions related to GDAL.
    Mostly alternatives to for bugs in arcpy.NumpyArrayToRaster.
    Projection definitions mostly still in arcpy.

Known limitations: python 3
---------------------------------------------------------------------------
"""
import os
import gdal
import arcpy

def ClipRaster(strPathIn, strPathOut, strBND, strComment):
    """ Clip raster.
        NOT YET WRITTEN
    """
    pass

def ArrayToRasterGDAL(arr, strPathRast, iDesc, strGDALdriver, strGDType):
    """ Save numpy array arr to raster strPathRast
        Return strPathRast.
    """
    if os.path.exists(strPathRast):
        raise Exception(f'ArrayToRasterGDAL, {strPathRast} already exists.')
            
    tupShape = arr.shape
    if len(tupShape) == 2:
        rows, cols = tupShape
        bands = 1
        arr = np.stack((arr,))
    elif len(tupShape) == 3:
        bands, rows, cols = tupShape

    pixelWidth, pixelHeight, originX, originY = iDesc.GDALdescribe

    driver = gdal.GetDriverByName(strGDALdriver)
    
    outRaster = driver.Create(strPathRast, cols, rows, bands, strGDType)
    # check below logic. Where is GDAL origin?
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))

    # write bands
    for b in range(1, bands + 1):
        outband = outRaster.GetRasterBand(b)
        outband.WriteArray(arr[b,:,:])
        outband.FlushCache()

    if iDesc.sr:
        arcpy.DefineProjection_management(strPathRast, iDesc.sr)
