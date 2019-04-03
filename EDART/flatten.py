"""
---------------------------------------------------------------------------
 flatten.py
 09/2018

 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 v1b. performing 'flattening' of EDART timing and confidence products

 Known limitations: python 3
---------------------------------------------------------------------------
"""
import os
import sys
import time
import numpy as np
import arcpy
import edart_utility as edU
import flatten_utility as flatU
sys.path.append(os.path.abspath(r'..\..\py3_general'))
import py3_general.generalARC as gARC
import py3_general.general as g
import py3_general.NDarrayUtility as NDarrU
import raster.rasterARCUtility as rastArcU

def flatten_conf(strOriginalPath, strWorkingPath, RASTEXT_, lstYears_, iOpt):
    """
        Options: See options class iOpt
    """
    strPathInYear = edU.get_EVTY(strOriginalPath)
    strPathInConf = edU.get_ConfEV(strOriginalPath)
    arcpy.env.workspace = strWorkingPath
    # lists of inetrmediates which may or may not be deleted at end
    lstIntermed = []

    # Ingest event and confidence bands from orig folder
    arcpy.env.workspace = strPathInYear
    lstYBNames = arcpy.ListRasters()
    intBands = len(lstYBNames)
    print('\n\t' + str(intBands) + ' event band(s) found.')
    arcpy.env.workspace = strWorkPath

    iDesc = gARC.getSimpleDesc(strPathInYear + os.sep + lstYBNames[0])

    print('\n\tIngesting event and confidence bands ...')
    t = time.time()
    arr3D_Conf = arcpy.RasterToNumPyArray(strPathInConf)
    arr3D_Evt = arcpy.RasterToNumPyArray(strPathInYear)

    arr3D_ConfM = np.where(arr3D_Conf >= 20, arr3D_Conf, 0)
    arr3D_EvtM = np.where(arr3D_Conf >= 20, arr3D_Evt, 0)
    print('\t\t', g.elapsed_time(t))

    print('\tRead confidence flags...')
    arrConfFlags = NDarrU.in_list(arr3D_Conf[0, :, :], lstConfidenceFlags)
    arrConfFlags = arrConfFlags.astype(np.int8)

    lstEventFOut, lstArrEventF = [], []
    lstConfFOut, lstArrConfF = [], []
    print('\n\tStarting years...')

    for y in lstYears_:
        t = time.time()
        print('\n\t\t' + str(y))
        if iOpt.bolDoAsMoistureYear:
            # test on moisture year
            arr3D_EvtM_bol = edU.testMoistureYear(arr3D_EvtM, y)
            strFileSuffix = '_Wat'
        else:
            # test on calendar year
            arr3D_EvtM_bol = edU.testYear(arr3D_EvtM, y)
            strFileSuffix = '_Cal'

        if iOpt.bolDoAsMaxConf:
            # filter for max conf event of the year
            arrOutEvent, arrOutConf = flatU.fMaxConfEV(arr3D_EvtM_bol, arr3D_EvtM, arr3D_ConfM)
        else:
            # filter for last event of the year
            arrOutEvent, arrOutConf = flatU.fLastEV(arr3D_EvtM_bol, arr3D_EvtM, arr3D_ConfM)
        arrOutConf = arrOutConf.astype(np.int8)

        # add in Confidence flags
        print('\tFlags...')
        # This will need som adjusting to get the right flags in.
        arrOutEventF = np.where(arrConfFlags, -1, arrOutEvent)
        arrOutConfF = np.where(arrConfFlags, arrConfFlags, arrOutConf)
        arrOutConfF = arrOutConfF.astype(np.int8)

        strEventFOut = 'Event_' + str(y) + strFileSuffix + RASTEXT_
        rastArcU.ArrayToRaster(arrOutEventF, strEventFOut, iDesc, val2NoData=-1, bolVerbose=False)
        lstEventFOut.append(strEventFOut)
        lstArrEventF.append(arrOutEventF)
        lstIntermed.append(strEventFOut)
        strConfFOut = 'Confidence_' + str(y) + strFileSuffix + RASTEXT_
        rastArcU.ArrayToRaster(arrOutConfF, strConfFOut, iDesc, bolVerbose=False)
        lstConfFOut.append(strConfFOut)
        lstArrConfF.append(arrOutConfF)
        lstIntermed.append(strConfFOut)

        print('\t\t\t', g.elapsed_time(t))
        
    # ---------------------------------------------------------
    # Optional outputs
    if iOpt.bolDoMaxConf or iOpt.bolDoSumConf:
        # This is max (highest) and sum of flattened confidences
        # so results will vary with flattening method
        arrOutConfND = np.stack(lstArrConfF)
        if iOpt.bolDoMaxConf:
            print('\tOptional: MaxConf...')
            strMaxConf = 'MaxConf' + strFileSuffix + RASTEXT_
            arrMax = arrOutConfND.max(axis=0)
            arrMaxF = np.where(arrConfFlags, arrConfFlags, arrMax)
            rastArcU.ArrayToRaster(arrMaxF, strMaxConf, iDesc, bolVerbose=False)
            del arrMax, arrMaxF

        if iOpt.bolDoSumConf:
            print('\tOptional: SumConf...')
            strSumConf = 'SumConf'+ strFileSuffix + RASTEXT_
            arrSum = arrOutConfND.sum(axis=0)
            arrSumF = np.where(arrConfFlags, arrConfFlags, arrSum)
            rastArcU.ArrayToRaster(arrSumF, strSumConf, iDesc, bolVerbose=False)
            del arrSum, arrSumF

        del arrOutConfND

    if iOpt.bolDoLastEV:
        # This is max (last) of flattened events
        # so results will vary with flattening method
        print('\tOptional: Last EV...')
        strLastEV = 'LastEV' + RASTEXT_
        arrOutEventND = np.stack(lstArrEventF)
        arrLast = arrOutEventND.max(axis=0)
        rastArcU.ArrayToRaster(arrLast, strLastEV, iDesc, bolVerbose=False)

        del arrOutEventND, arrLast

    return lstEventFOut, lstConfFOut, strFileSuffix

# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # ------------------------------
    # User Variables
    lstOrigPath = [r'N:\project\EDART_vol\edartOps\data\sc_ca\sc305ns_v4',
                   r'N:\project\EDART_vol\edartOps\data\sc_ca\sc306ns_v3',
                   r'N:\project\EDART_vol\edartOps\data\sc_ca\sc307ns_v3',
                   r'N:\project\EDART_vol\edartOps\data\sc_ca\sc309ns_v5']

    # Output raster file extention
    RASTEXT = '.tif'
    # Start and end years (inclusive)
    intYearStart = 2008
    intYearEnd = 2018
    # Options
    bolRedoExisting = False
    bolDoAsMoistureYear = False
    bolDoSumConf = True
    bolDoMaxConf = True
    bolDoLastEV = False
    bolStackOutputs = True
    strScratchWS = r'E:\swap2'
    # confidence flags (Don't change)
    lstConfidenceFlags = [-1, 1, 2]

    # ------------------------------
    lstYears = range(intYearStart, intYearEnd + 1)
    if os.path.exists(strScratchWS):
        arcpy.env.scratchWorkspace = strScratchWS

    for strOrigPath in lstOrigPath:
        strOrigPath = edU.expand2TDISpath(strOrigPath)
        print('\n' + strOrigPath)
        strSuf = '_CalenderYear'
        if bolDoAsMoistureYear:
            strSuf = '_WaterYear'
        strWorkPath = edU.prep_workspace(strOrigPath, 'flattenConf' + strSuf,
                                         bolRedo_=bolRedoExisting)

        if strWorkPath:
            iOptions = flatU.flattenOptions(strWorkPath, bolRedoExisting, bolDoAsMoistureYear,
                                            bolDoSumConf, bolDoMaxConf, bolDoLastEV)
            iOptions.record()

            lstRastEVT, lstRastConf, strFileSuf = flatten_conf(strOrigPath, strWorkPath, RASTEXT,
                                                               lstYears, iOptions)

            if bolStackOutputs:
                print('\tStacking:')
                print('\t\tEvents..')
                strPathEventStacked = strWorkPath + os.sep + edU.EVENTSUFFIX + '_PerYear' + strFileSuf + RASTEXT
                rastArcU.StackRaster(lstRastEVT, strPathEventStacked)
                print('\t\tConfidence..')
                strPathConfStacked = strWorkPath + os.sep + edU.CONFSUFFIX + '_PerYear' + strFileSuf + RASTEXT
                rastArcU.StackRaster(lstRastConf, strPathConfStacked)
        else:
            print('\t\tAlready done. Skipping.')
            
    print('Done.')
