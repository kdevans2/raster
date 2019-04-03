"""
---------------------------------------------------------------------------
 flatten_utility.py
 09/2018

 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 supporting functions and classes for 'flattening' of EDART timing and confidence products

 Known limitations: python 3
---------------------------------------------------------------------------
"""
import os
import numpy as np
import edart_utility as edU

def fLastEV(arr3_EvtM_bol, arr3_Evt, arr3_Conf):
    """ Return last Event and its corresponding confidence, given
            arr3_EvtM_bol already masked to year of interest.
    """
    print('\t\tStats (last EV)...', end='')
    arr3_EvtM_bolY = arr3_EvtM_bol * arr3_Evt
    arrOutYearMax = arr3_EvtM_bolY.max(axis=0)
    print('\tGet matching confidence...', end='')
    arrOutConf = np.zeros(arrOutYearMax.shape)
    for b in range(arr3_EvtM_bolY.shape[0]):
        arrOutConf = np.where(arrOutYearMax == arr3_Evt[b, :, :],
                              arr3_Conf[b, :, :], arrOutConf)

    return arrOutYearMax, arrOutConf

def fMaxConfEV(arr3_EvtM_bol, arr3_Evt, arr3_Conf):
    """ Return highest confidence and its corresponding timing, given
            arr3_EvtM_bol already masked to year of interest.
            Something in this fuction or calling it is broken.
    """
    print('\t\tStats (max conf)...', end='')
    arr3_ConfM_bolY = arr3_EvtM_bol * arr3_Conf
    arrOutConfMax = arr3_ConfM_bolY.max(axis=0)
    print('\tGet matching event...', end='')
    arrOutEvent = np.zeros(arrOutConfMax.shape)
    for b in range(arr3_ConfM_bolY.shape[0]):
        arrOutEvent = np.where(arrOutConfMax == arr3_ConfM_bolY[b, :, :],
                               arr3_Evt[b, :, :], arrOutEvent)

    return arrOutEvent, arrOutConfMax

def fMinPPEV(arr3_EvtM_bol, arr3_Evt, arr3_PP):
    """ Return minimum Pre-Post difference and its corresponding timing, given
            arr3_EvtM_bol already masked to year of interest.
            Something in this fuction or calling it is broken.
    """
    print('\t\tStats (min PrePostDif)...', end='')
    arr3_PPM_bolY = np.where(arr3_EvtM_bol, arr3_PP, 10003)
    arrOutPPMin = arr3_PPM_bolY.min(axis=0)
    print('\tGet matching event...', end='')
    arrOutEvent = np.ones(arrOutPPMin.shape) * 10004
    for b in range(arr3_PPM_bolY.shape[0]):
        arrOutEvent = np.where(arrOutPPMin == arr3_PPM_bolY[b, :, :],
                               arr3_Evt[b, :, :], arrOutEvent)

    return arrOutEvent, arrOutPPMin

class flattenOptions:
    """ Container for ProcessScene options. """
    def __init__(self, strPath, boolRedoExisting, boolDoAsMoistureYear,
                 boolDoSumConf, boolDoMaxConf, boolDoLastEV):
        """ init """
        self.path = strPath
        self.bolRedoExisting = boolRedoExisting
        self.bolDoAsMoistureYear = boolDoAsMoistureYear
        self.bolDoSumConf = boolDoSumConf
        self.bolDoMaxConf = boolDoMaxConf
        self.bolDoLastEV = boolDoLastEV

        if self.bolDoAsMoistureYear:
            self.bolDoAsMaxConf = False
            self.bolDoAsMinPP = False
        else:
            self.bolDoAsMaxConf = False
            self.bolDoAsMinPP = False

    def record(self, strPathTxt=None):
        """ save settings to strPathTxt. """
        if strPathTxt is None:
            strPathTxt = self.path + os.sep + 'a_RunPARAMETERS.txt'
        with open(strPathTxt, 'w') as txt:
            try:
                txt.write(__file__ + '\n')
            except NameError:
                pass
            txt.write('Run parameters:\n')
            for k in self.__dict__:
                txt.write(f'{k}: {self.__dict__[k]}\n')

    def __str__(self):
        """ str method """
        for k in self.__dict__:
            print(f'{k}: {self.__dict__[k]}\n')

def StatConfTotal(arr3D_Evt, arr3D_Conf, intYearS, intYearE, fStat, arrConfFlags=None):
    """ Return 0 axis statistic (fStat, typically np.sum or np.max) of
            confidence array for of all events from intYearS to intYearE (inclusive).
        Should also work like old MaxConf or SumConf, if given flattened events and confidences.
    """
    if arr3D_Evt.shape != arr3D_Conf.shape:
        raise Exception('SumConfTotal, arr3D_EvtM and arr3D_ConfM shape must match.')
    if arrConfFlags and len(arrConfFlags.shape) != 2:
        raise Exception('SumConfTotal, arrConfFlags must be 2D.')

    arrYtest = edU.testYear(arr3D_Evt, intYearS, intYearE)
    arrStat = fStat((arrYtest * arr3D_Conf), axis=0)

    if arrConfFlags:
        # Add back flags
        arrStat = np.where(arrConfFlags, arrConfFlags, arrStat)

    del arrYtest
    return arrStat
