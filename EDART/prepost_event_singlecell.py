"""
---------------------------------------------------------------------------
 prepost_event_SingleCell2.py
 02/2019

 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 script to:

 Known limitations: python 3.6
---------------------------------------------------------------------------
"""
import os
import datetime as dt
import numpy as np
import pandas as pd
import arcpy
import edart_utility as edU
import prepost_utility as ppU
import prepost_readwrite as ppRW

def prep_alt(strOriginalPath, strWorkingPath, BANDNAME_, sPathFC, tCornerOffset_, lRawDates_=None):
    """ Prep data. Get array stack for given BANDNAME_ and extract
            samples given in sPathFC to text files.
            sPathFC is a point feature class containing projected X and Y fields.
    """
    iCELLSIZE = 30
    Xp0, Yp0 = tCornerOffset_
    # load rasters
    strPathScene = edU.getSceneDir(strOriginalPath)
    strPath_nFrEV = edU.get_nFrEV(strOriginalPath)
    arcpy.env.workspace = strWorkingPath
    print('\n\tIngesting Frame EVT raster...')
    arr3D_FrEV = arcpy.RasterToNumPyArray(strPath_nFrEV)
    print('\t\tFrEV shape: ', arr3D_FrEV.shape)
    a3D_Index, a3D_Mask, dEvLU_, dDateLU_ = edU.IngestFramesPartial(strPathScene, BANDNAME_,
                                                                    arr3D_FrEV.shape[1:],
                                                                    lRawDates=lRawDates_,
                                                                    bReturnDateLU=True)

    print('Reading samples...\n')
    dSamplesText_ = {}
    with arcpy.da.SearchCursor(sPathFC, ('ROIID', 'x', 'y')) as rows_:
        for row_ in rows_:
            sROIID = row_[0]

            print(sROIID)
            if sROIID is None:
                print('\tNo ROIID, Skipping.')
                continue

            strPathTXT = ppRW.ROIID_txt_name(sROIID, BANDNAME_, 'extract_files')
            if os.path.exists(strPathTXT):
                print('\tROIID already done.')
                continue

            if not os.path.exists(os.path.dirname(strPathTXT)):
                os.makedirs(os.path.dirname(strPathTXT))

            print('\t', strPathTXT)
            Xp, Yp = row_[1:]
            X = int((Xp - Xp0) / iCELLSIZE)
            Y = int(-(Yp - Yp0) / iCELLSIZE)
            aIndex_ = a3D_Index[:, Y, X]
            aMask_ = a3D_Mask[:, Y, X]

            dfSample = pd.DataFrame({'Index':aIndex_, 'Mask':aMask_})
            dfSample.to_csv(strPathTXT, index=False)
            dSamplesText_[sROIID] = strPathTXT

    del arr3D_FrEV, a3D_Index, a3D_Mask
    return dSamplesText_, dEvLU_, dDateLU_

# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # ------------------------------
    # User Variables
    sOrigPath = r'D:\p_data\edartOps\data\sc_dev\sc5rse_v03\envi_aux\TDIS\TDISm__r180821_1945_93fr_180822-0554'
    sPathWork = r'N:\project\EDART_vol\projects\MMI'
    sXL = 'test_evt_sc5_20190315.xlsx'
    sSheetName = 'TotalSample'
    sPathSHP = r'shapes\sc5_validation_plots_20190315.shp'
    tCornerOffset = (246480, 4134660)
    sPathDates = 'lstdates.txt'
    sResultsTxt = f'results_20190315.csv'
    sResultsTxtT = f'results_20190315_T.csv'

    # number of samples needed
    iSampleMin = 5
    # list of bandnames
    lBANDNAME_z2 = ['z2_NBR', 'z2_NDVI', 'z2_NDII', 'z2_TCA', 'z2_RGA']
    lBANDNAME_r2 = ['r2_NBR', 'r2_NDVI', 'r2_NDII', 'r2_TCA', 'r2_RGA']
    lBANDNAME_raw = ['NDVI', 'NDII', 'NBR', 'TCA', 'RGA']
    lBANDNAME = lBANDNAME_z2 + lBANDNAME_r2
    tDropZerosSlice = (0, 5)

    # Options
    strSCRATCH = r'D:\swap2'
    arcpy.env.workspace = strSCRATCH
    sPrePrefix = 'MedianPre'
    sPostPrefix = 'MedianPost'
    lPref = [sPrePrefix, sPostPrefix]
    lHeaderSub = [f'{sPref}_{sBN}' for sBN in lBANDNAME for sPref in lPref]
    lHeader = ['ROIID'] + lHeaderSub + ['comment', 'details1', 'details2']

    # ------------------------------
    if os.path.exists(strSCRATCH):
        arcpy.env.scratchWorkspace = strSCRATCH

    sOrigPath = edU.expand2TDISpath(sOrigPath)
    print('\n' + sOrigPath)

    os.chdir(sPathWork)

    xl = pd.ExcelFile(sXL)
    dfXL = xl.parse(sSheetName)

    aDatesRaw = ppRW.read_datetext(sPathDates)
    lDatesRaw = [d.isoformat().replace('-', '.') for d in list(aDatesRaw)]

    # Residuals extract
    for sBN in (lBANDNAME_z2 + lBANDNAME_r2)[:1]:
        dSamplesText, dicEvLU, dicEvLUdate = prep_alt(sOrigPath, sPathWork, sBN,
                                                      sPathSHP, tCornerOffset)

    dfOut = pd.DataFrame(columns=lHeader)
    for i in range(dfXL.shape[0]):
        srXL = dfXL.iloc[i]
        print(i, srXL.ROIID)
        srOut = pd.Series(index=lHeader)
        srOut.ROIID = srXL.ROIID
        sComment = ''
        lDetail1 = ['', '']
        lDetail2 = ['', '']

        lPathTxt = [ppRW.ROIID_txt_name(srXL.ROIID, sBN, 'extract_files') for sBN in lBANDNAME]

        if False in [os.path.exists(f) for f in lPathTxt]:
            print('\tNot extracted')
            dfOut = ppRW.appendSeries(srOut, dfOut, 'Not extracted')
            continue

        if pd.isna(srXL.t_pre) or pd.isna(srXL.t_post):
            print('\tMissing t_pre or t_post')
            dfOut = ppRW.appendSeries(srOut, dfOut, 'Missing t_pre or t_post')
            continue

        aInd, aMask = ppRW.read_ROIID_texts(lPathTxt)

        # Drop masked values
        aInd, aDates_m = ppU.drop_masked(aInd, aMask, aDatesRaw)
        # Drop all zero z2 dates
        aInd, aDates_m = ppU.drop_zeros(aInd, aDates_m, tDropZerosSlice)
        # get dates and split pre and post
        d0 = ppU.timestamp_to_date(srXL.t_pre)
        d1 = ppU.timestamp_to_date(srXL.t_post)
        aInd_pre, aD_pre = ppU.split_pre(aInd, aDates_m, d0)
        aInd_post, aD_post = ppU.split_post(aInd, aDates_m, d1)

        if aInd_pre.shape[0] == 0 or aInd_post.shape[0] == 0:
            dfOut = ppRW.appendSeries(srOut, dfOut, 't_pre or t_post leaves zero length time frame')
            continue

        aMedians = np.zeros((2, len(lBANDNAME)))

        lEnum = [[aInd_pre, aD_pre, sPrePrefix], [aInd_post, aD_post, sPostPrefix]]
        for j, (aInd_m, aD_m, sPrefix) in enumerate(lEnum):
            lDates = aD_m[ppU.isMonthV(aD_m)].tolist()[:iSampleMin]
            lStat = aInd_m[ppU.isMonthV(aD_m)].tolist()[:iSampleMin]

            # record length of prefered August September slice
            lDetail1[j] = (len(lStat))

            if len(lStat) < iSampleMin:
                #print('\tTake non-summer')
                lIndNotSummer = aInd_m[~ppU.isMonthV(aD_m)].tolist()
                lDatesNotSummer = aD_m[~ppU.isMonthV(aD_m)].tolist()
                lDates += lDatesNotSummer[:iSampleMin - len(lStat)]
                lStat += lIndNotSummer[:iSampleMin - len(lStat)]

            # record medians
            srOut[[f'{sPrefix}_{sBN}' for sBN in lBANDNAME]] = np.median(np.array(lStat), axis=0)

            # record width of window used for median
            dtdRange = max(lDates) - min(lDates)
            lDetail2[j] = int(dtdRange / dt.timedelta(days=1))

            # comment if median was drawn from less than 5 samples
            if len(lStat) < iSampleMin:
                sComment = f'Short pre or post time frame: {len(lStat)}'

        # append results to dataframe
        srOut.details1 = f'{lDetail1[0]};{lDetail1[1]}'
        srOut.details2 = f'{lDetail2[0]};{lDetail2[1]}'
        dfOut = ppRW.appendSeries(srOut, dfOut, sComment)

    dfOut.to_csv(sResultsTxt, index=False)
    
    df4RGA = pd.read_csv(sResultsTxt)
    sBand = 'r2_RGA'
    lColumn = [f'MedianPre_{sBand}', f'MedianPost_{sBand}']
    lColumnT = [f'MedianPre_{sBand}_T', f'MedianPost_{sBand}_T']
    df4RGA = ppU.add_transformed_rga(df4RGA, lColumn, lColumnT)
    df4RGA.to_csv(sResultsTxtT)

    print('\nDone.')
