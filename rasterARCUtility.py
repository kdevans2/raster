"""
---------------------------------------------------------------------------
 rasterARCUtility.py
 09/2018
 
 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 raster functions related to ARCGIS Pro

 Known limitations: python 3
---------------------------------------------------------------------------
"""
import os
import arcpy

def printD(s, bolVerbose = True):
    """ Print, with option to supress.
        Temp work arround for Shengli's commments in ArrayToRaster
    """
    if bolVerbose:
        print(s)

def ClipRaster(strPathIn, strPathOut, strBND, strComment):
    ''' Clip raster. '''
    if arcpy.Exists(strPathOut):
        return strPathOut
    
    arcpy.Clip_management(strPathIn, strBND, out_raster=strPathOut)

    return strPathOut


def CropRaster(strPathIn, strPathOut, intBuf, fltCellSize, intCells, iTile, strComment):
    """ Clip a specified number of pixels of edge of raster.
        For use by LiDAR processing with iTile object.
    """
    if arcpy.Exists(strPathOut):
        return strPathOut
    arcpy.env.pyramid = 'NONE'
    
    MinX = str(iTile.XMin - intBuf + fltCellSize * intCells )
    MinY = str(iTile.YMin - intBuf + fltCellSize * intCells )
    MaxX = str(iTile.XMax + intBuf - fltCellSize * intCells )
    MaxY = str(iTile.YMax + intBuf - fltCellSize * intCells )
    strBND = ' '.join([MinX,MaxY,MaxX,MinY])
    arcpy.Clip_management(strPathIn, strBND, strPathOut)

    return strPathOut


def StackRaster(lstRastIn, strPathOut):
    """ arcpy.Composite bands and rename bands to match input rasters. """
    arcpy.CompositeBands_management(';'.join(lstRastIn), strPathOut)
    
    for i, rast in enumerate(lstRastIn):
        strBNin = 'Band_' + str(i + 1)
        strBNout = os.path.splitext(os.path.basename(rast))[0]
        arcpy.Rename_management(strPathOut + os.sep + strBNin, strPathOut + os.sep + strBNout)

# ---------------------------------------------------------------------------
# Math
def Round(rastIn):
    ''' Round spatial analyst raster.
        Curently only for positive values.
    '''
    rastUp = arcpy.sa.RoundUp(rastIn)
    rastDown = arcpy.sa.RoundDown(rastIn)

    rastOut = arcpy.sa.Con( (rastUp - rastIn) <= 0.5, rastUp, rastDown)
    return arcpy.sa.Int(rastOut)

# ---------------------------------------------------------------------------
# Simple describe object
def getSimpleDesc(strPathRast):
    """ Get raster properties and place into SimpleDesc. """
    desc = arcpy.Describe(strPathRast)
    fltCellSize_X = desc.meanCellWidth
    fltCellSize_Y = desc.meanCellHeight
    if not fltCellSize_X == fltCellSize_Y:
        raise Exception('Non square cell size.')
    
    pt = arcpy.Point(desc.extent.XMin, desc.extent.YMin)
    sr = desc.spatialreference
    return SimpleDesc(ptLL = pt, fltCellSize = fltCellSize_X, SR = sr,
                      intWidth = desc.width, intHeight = desc.height)

class SimpleDesc():
    """ Simple class to contain properties needed for writing numpy array to raster. """
    def __init__(self, ptLL = None, fltCellSize = None, SR = None, val2NoData = None,
                 intWidth = None, intHeight = None):
        self.ptLL = ptLL
        self.CellSize = fltCellSize
        self.sr = SR
        self.val2NoData = val2NoData
        self.width = intWidth
        self.height = intHeight
        self.shape = (intHeight, intWidth)
        self.Xmin = self.ptLL.X
        self.Ymin = self.ptLL.Y
        if intWidth and intHeight:
            self.Xmax = self.ptLL.X + self.CellSize * self.width
            self.Ymax = self.ptLL.Y + self.CellSize * self.height

    def SetLL(self, ptLLnew):
        """ Helper function for ptLL property. """
        self.ptLL = ptLLnew

    def SetVal2NoData(self, val2NoData):
        """ Helper function for val2NoData property. """
        self.val2NoData = val2NoData

    def describe(self):
        """ Return sequence of propertries as needed by:
                arcpy.NumpyArrayToRaster.
        """
        return self.ptLL, self.CellSize, self.CellSize

    def Extent(self):
        """ Return arcpy extent object. """
        return arcpy.Extent(self.Xmin, self.Ymin, self.Xmax, self.Ymax)

    def describeGDAL(self):
        """ Return sequence of propertries as needed by:
                gdal.GetDriverByName().Create().SetGeoTransform
            Check order of outputs vs SetGeoTransform
        """
        return (originX, self.CellSize, 0, originY, 0, self.CellSize)

# ---------------------------------------------------------------------------
# numpy related
def ArrayToRaster(arr, strPathRast, iDesc, val2NoData = None, bolVerbose = True):
    """ Save numpy array arr to raster strPathRast
        Return strPathRast.
    """
    if not os.path.exists(strPathRast):
        printD('Kirk ArrayToRaster 1', bolVerbose)
        rastSave = arcpy.NumPyArrayToRaster(arr, *iDesc.describe(), value_to_nodata = val2NoData)
        printD('Kirk ArrayToRaster 2', bolVerbose)
        printD('On July 20, 2018, we found: 1) tif in tif out: OK; 2)tif in img out: bad; 3)img in tif out: OK; 4)img in img out: bad. so img can not be output format', bolVerbose)
        arcpy.CopyRaster_management(rastSave, strPathRast)  
        printD('Kirk ArrayToRaster 3', bolVerbose)
        arcpy.DefineProjection_management(strPathRast, iDesc.sr)
        printD('Kirk ArrayToRaster 4', bolVerbose)
        arcpy.Delete_management(rastSave)
        printD('Kirk ArrayToRaster 5', bolVerbose)
    else:
        print('Already saved: ' + strPathRast)
