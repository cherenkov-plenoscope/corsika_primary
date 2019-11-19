import numpy as np
import os

class CherenkovInOut(object):

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self._file_size = os.path.getsize(path)
        self._photon_size = 16
        self._number_of_photons = int(self._file_size/self._photon_size)
        self._compressed_photon_dtype = np.dtype([
           ('x', np.int16),
           ('y', np.int16),
           ('cx', np.int16),
           ('cy', np.int16),
           ('arrival_time', np.float32),
           ('wavelength', np.int8),
           ('mother_charge', np.int8),
           ('emission_altitude', np.int16),
        ])
        self.current_photon = 0


    def __repr__(self):
        out = 'CherenkovInOut('
        out+= self.path+', '
        out+= str(self._number_of_photons)+' photons'
        out+= ')'
        return out


    def next_block(self, number_of_photons=1000*1000):
        start = self.current_photon
        end = start+number_of_photons

        if end > self._number_of_photons:
            end = self._number_of_photons

        photons = self._get_photons_from_until(start, end)
        self.current_photon = end
        return photons


    def seek_to_photon(self, seek):
        self.current_photon = seek


    def _get_raw_photons_from_until(self, start, end):

        if end > self._number_of_photons:
            raise StopIteration

        if start > self._number_of_photons:
            raise StopIteration

        startByte = self._photon_size*start
        endByte = self._photon_size*end
        numberBytes = endByte - startByte
        numberRows = end - start 

        f = open(self.path, 'rb')
        f.seek(startByte)
        raw = f.read(numberBytes)
        f.close()

        raw_photons = np.fromstring(raw, dtype=self._compressed_photon_dtype)
        return raw_photons


    def _get_photons_from_until(self, start, end):
        raw_photons = self._get_raw_photons_from_until(start, end)
        return self._decompress_photons(raw_photons)


    def _decompress_photons(self, raw_photons):
        photons = np.zeros(shape=(raw_photons.shape[0] ,8), dtype=np.float32)
        int16max = 32767.0
        int8max = 255.0
        photons[:,0] = (raw_photons['x']/int16max)*260.0e2
        photons[:,1] = (raw_photons['y']/int16max)*260.0e2
        photons[:,2] = raw_photons['cx']/int16max
        photons[:,3] = raw_photons['cy']/int16max
        photons[:,4] = raw_photons['arrival_time']
        photons[:,5] = (raw_photons['wavelength']/int8max)*1e3 + 2e2
        photons[:,6] = raw_photons['mother_charge']
        photons[:,7] = (raw_photons['emission_altitude']/int16max)*100*1e3*1e2
        return photons