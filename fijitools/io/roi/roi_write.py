# -*- coding: utf-8 -*-
"""
@author: Vladimir Shteyn
@email: vladimir.shteyn@googlemail.com

Copyright Vladimir Shteyn, 2018

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
# import pandas as pd
import zipfile
import h5py
import os
import io
from abc import abstractmethod

from fijitools.io import IO


class Writer(IO):
    @abstractmethod
    def write(self, *args, **kwargs):
        pass


class IJZipWriter(Writer):
    """
    From an instance of an roi_objects.BaseROI subclass, generate
    a zip file containing ROI bytestreams readable by ImageJ.

    Parameters
    -----------
    zip_path: str
    Filename.
    """

    def __init__(self, zip_path):
        self.path = zip_path
        self._file = zipfile.ZipFile(zip_path, 'a')

    def write(self, roi, roi_name, image_name='', as_roi_class=None):
        """
        Parameters
        -----------
        roi: roi_objects.BaseROI child class

        roi_name: str

        image_name: str

        as_roi_class: roi_objects.BaseROI child class

        """
        if as_roi_class:
            data = as_roi_class.to_IJ(roi, roi_name, image_name)
        else:
            data = roi.to_IJ(roi, roi_name, image_name)
        self._file.write(io.BytesIO(data))

    def cleanup(self):
        self._file.close()


class Hdf5Writer(Writer):
    """
    Modified from the accepted answer at:
    https://preview.tinyurl.com/yc5j75wr
    """
    def __init__(self, h5path):
        self._file = h5py.File(h5path)
        self.data_length = None

    def write(self, roi, image_name, attrs):
        """
        """
        data = roi.to_nested_dict(attrs, image_name, attrs[-1])
        self._recursively_save_dict_contents_to_group('/', data)

    def _recursively_save_dict_contents_to_group(self, path, dic):
        """
        """
        for key, val in dic.items():
            if isinstance(val, dict):
                self._recursively_save_dict_contents_to_group(path + key + '/',
                                                              val)
            elif isinstance(val, np.ndarray):
                if self.data_length is None:
                    self.data_length = len(val)
                elif not len(val) == self.data_length:
                    e = 'Data must be length {}. '.format(self.data_length) + \
                        'A value of length {} was passed in.'.format(len(val))
                    raise TypeError(e)
                self._file[path + key] = val
            elif isinstance(val, (np.int64, np.float64, str, bytes)):
                if self.data_length is None:
                    self.data_length = 1
                elif not self.data_length == 1:
                    e = 'Data must be array of length '
                    '{}. A scalar was passed in.'.format(self.data_length)
                    raise TypeError(e)
                self._file[path + key] = val
            else:
                raise ValueError('Cannot save {} type.'.format(val))

    def cleanup(self):
        # convert ROI data to sparse arrays
        self._file.close()

    # I'm sure this will become useful later...
    # @classmethod
    # def load_dict_from_hdf5(cls, filename):
    #     """
    #     ....
    #     """
    #     with h5py.File(filename, 'r') as h5file:
    #         return cls.recursively_load_dict_contents_from_group(h5file, '/')

    # @classmethod
    # def recursively_load_dict_contents_from_group(cls, h5file, path):
    #     """
    #     ....
    #     """
    #     ans = {}
    #     for key, item in h5file[path].items():
    #         if isinstance(item, h5py._hl.dataset.Dataset):
    #             ans[key] = item.value
    #         elif isinstance(item, h5py._hl.group.Group):
    #             ans[key] = cls.recursively_load_dict_contents_from_group(h5file, path + key + '/')
    #     return ans
