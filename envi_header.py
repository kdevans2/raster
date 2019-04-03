""" 
----------------------------------------------------------------------------------------
 envi_header.py
 06/2018
 
 Kirk Evans, GIS Analyst/Programmer, TetraTech EC @ USDA Forest Service R5/Remote Sensing Lab
   3237 Peacekeeper Way, Suite 201
   McClellan, CA 95652
   kdevans@fs.fed.us

 script to: class HDR to support use of ENVI raster ().bsq header files.

 Known limitations: python 3
----------------------------------------------------------------------------------------
"""
import os

class HDR():
    """ Class to ingest and store all items in ENVI raster header file.
        Tested ONLY on bsq rasters saved by MATLAB!
    """
    def __init__(self, strPathRast):
        """ Initialize HDR class """
        self.raster = strPathRast
        self.header_file = os.path.splitext(strPathRast)[0] + '.hdr'

        self._ingestHDR()
        self._cleanHDR()

        # set attributes with dictionary
        self.__dict__.update(self.dicAttr)
        lstMapInfo = [v.strip() for v in self.map_info.split(',')]
        self.XMin = float(lstMapInfo[3])
        self.YMax = float(lstMapInfo[4])
        
        self.CellSizeX = float(lstMapInfo[5])
        self.CellSizeY = float(lstMapInfo[6])
        if self.CellSizeX == self.CellSizeY:
            self.CellSize = self.CellSizeX

        if 'lines' in self.__dict__:
            self.lines = int(self.lines)
            self.YMin = self.YMax - self.CellSizeY * self.lines

        if 'samples' in self.__dict__:
            self.samples= int(self.samples)
            self.XMax = self.XMin + self.CellSizeX * self.samples

    def _ingestHDR(self):
        """ Ingest header file to dictionary """
        dicHDR = {}
        with open(self.header_file) as hdr:
            bolMulti = False
            for line in hdr.readlines():
                line = line.strip()
                if ' = {' in line:
                    bolMulti = True
                    bolMultiStart = True

                if not bolMulti:
                    try:
                        item, value = line.split(' = ')
                    except ValueError:
                        continue
                    dicHDR[item] = value

                else:
                    if bolMultiStart:
                        item, value = line.split(' = ')
                        item = item.strip()
                        value = value.lstrip('{').rstrip('}').rstrip(',').strip()

                        dicHDR[item] = [value]
                        bolMultiStart = False
                    else:
                        value = line.rstrip(',').rstrip('}')
                        dicHDR[item].append(value)

                if line[-1] == '}':
                    bolMulti = False

        self.dicAttr = dicHDR

    def _cleanHDR(self):
        """ In situ clean spaces from attribute names (keys) and reduce single item lists. """
        for k in self.dicAttr:
            val = self.dicAttr[k]
            if type(val) == list and len(val) == 1:
                self.dicAttr[k] = val[0]
                
            if ' ' in k:
                kNew = k.replace(' ', '_')
                self.dicAttr[kNew] = self.dicAttr[k]
                del self.dicAttr[k]
                
    def bandName_wild(self, strWild):
        """ Return band name containing strWild. """
        lstIndex = [b for b in self.band_names if strWild in b]
        if len(lstIndex) == 0:
            raise Exception(strWild + 'not found in band_names.')
        elif len(lstIndex) > 1:
            raise Exception(strWild + 'not unique in band_names.')
        return lstIndex[0]
    
