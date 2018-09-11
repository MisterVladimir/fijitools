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
import pandas as pd
import re
import zipfile
import os
from struct import unpack, unpack_from
from collections import OrderedDict
from addict import Dict

from fijitools.helpers.data_structures import IndexedDict
from fijitools.io import IO
from fijitools.io.roi import (HEADER_SIZE, HEADER2_SIZE,
                              HEADER_DTYPE, HEADER2_DTYPE,
                              COLOR_DTYPE, OPTIONS,
                              SUBTYPE, ROI_TYPE, COLOR_DTYPE,
                              SELECT_ROI_PARAMS)
from fijitools.io.roi.roi_objects import ROI


class Reader(IO):
    pass


class IJZipReader(Reader):
    """
    The goal is to convert ImageJ/FIJI ROI bytestreams to human-readable data
    using python. Unlike other libraries I'm aware of, here we let numpy do
    the heavy lifting of converting bytestream to bytes, shorts, integers, and
    floats. Strings, e.g. the ROI name, are unpacked using the struct library.
    This information is stored as a numpy.recarray. See global variables
    imported from roi.__init__ to understand which position in the bytestream
    corresponds to which ROI parameters.

    Inspiration from:
    https://github.com/hadim/read-roi/
    https://github.com/DylanMuir/ReadImageJROI

    And from the ImageJ Java code:
    https://github.com/imagej/ImageJA/blob/master/src/main/java/ij/io/RoiEncoder.java
    https://github.com/imagej/ImageJA/blob/master/src/main/java/ij/io/RoiDecoder.java

    Parameters
    -----------
    regexp: str
    Argument for re.compile() to filter roi names within the zip file.

    sep: str
    ROI data may be grouped, for example by the biological structure they
    label. Because multiple members of one group may be found in one image, the
    user may specify group names in the ROI name according to the following
    format: [class][sep][integer]. If sep is not None -- in which case every
    ROI is read as a distinct group -- then IJRoiDecoder stores ROI data in
    nested dictionary format.
    """

    def __init__(self, regexp='.*roi$', sep=None):
        self.regexp = re.compile(regexp)
        self.sep = sep
        self.data = IndexedDict()

    @property
    def paths(self):
        return list(self.data.keys())

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def read(self, path, pwd=None, name=None):
        """
        Parameters
        -----------
        path: str
        Path to the file.

        pwd: str
        Zip files may be password protected.

        name: str
        How to (re)name the zip file's data. If left as None, name is the file
        name.
        """
        if name is None:
            name = os.path.basename(path).split(os.path.extsep)[0]
        self.data[name] = IndexedDict()
        # reads all the zip files' byte streams, sends them to parsing function
        self._file = zipfile.ZipFile(path, 'r')
        filelist = [f for f in self._file.namelist() if self.regexp.match(f)]
        streams = [None]*len(filelist)
        for i, roi_name in enumerate(filelist):
            with self._file.open(roi_name, 'r') as f:
                streams[i] = f.read()

        # file type checking: .roi files' first four bytes encode 'Iout'
        self.bytestreams = [s for s in streams if s[:4] == b'Iout']
        self._parse_bytestream(name)

    def _parse_bytestream(self, filename):
        """
        Note that much of the bytestream data is not actually needed for
        creating ROI objects (see roi_objects module). Much of the bytestream
        data is therefore ignored.
        """
        # parse header data
        hdr_buffer = b''.join([b[:HEADER_SIZE] for b in self.bytestreams])
        hdr = np.frombuffer(hdr_buffer, HEADER_DTYPE)

        hdr2_offsets = hdr['hdr2_offset']
        hdr2_buffer = b''.join([bs[off:off+HEADER2_SIZE]
                                for off, bs in zip(hdr2_offsets,
                                                   self.bytestreams)])
        hdr2 = np.frombuffer(hdr2_buffer, HEADER2_DTYPE)

        name_offsets = hdr2['name_offset']
        name_lengths = hdr2['name_length']
        # assumes characters are ascii-encoded...
        names = self._get_names(name_offsets, name_lengths)
        # determine if subpixel resolution
        subpixel = np.logical_and(hdr['options'] & OPTIONS['subpixel'],
                                  hdr['version'] >= 222)
        bounding_rect = self._get_bounding_rect(hdr, subpixel)
        # parse parameters common to all ROI
        common = self.get_common(hdr, hdr2)
        points = self._get_points(hdr, subpixel)
        # roi properties encoded at the end of the bytestream
        props = self._get_roi_props(hdr['hdr2_offset'],
                                    hdr2['roi_props_offset'],
                                    hdr2['roi_props_length'])

        for br, com, p, pr, typ, name in zip(bounding_rect, common, points,
                                             props, hdr['type'], names):
            if name[1]:
                self.data[filename][name[0]][name[1]] = ROI(
                                                         br, com, p, pr, typ)
            else:
                self.data[filename][name[0]] = ROI(br, com, p, pr, typ)

    def _get_names(self, offsets, lengths):
        """
        Decode roi names from the bytestream. If a self.sep is provided,
        tokenize names into ROI Group / Index pairs. Otherwise, set the
        Index to an empty string.
        """
        names = ["".join(map(chr, unpack_from('>'+'h'*le, bs, offset=off))) for
                 bs, off, le in zip(self.bytestreams, offsets, lengths)]
        if self.sep:
            names = [name.split(self.sep) for name in names]
            return [li + [''] if len(li) == 1 else li for li in names]
        else:
            return [[n, ''] for n in names]

    def _get_bounding_rect(self, hdr, subpixel):
        """
        Use subpixel resolution coordinates -- 
        field names '['y1', 'x1',  'y2', 'x2']' -- where they are available. 
        Otherwise, coerce to float32.
        """
        dtype = [('x0', 'f4'), ('y0', 'f4'), ('x1', 'f4'), ('y1', 'f4')]
        coords = np.where(
            np.repeat(subpixel[:, None], 4, 1),
            hdr[['y1', 'x1',  'y2', 'x2']].astype(dtype).view(
                'f4').reshape((-1, 4)),
            hdr[['left', 'top', 'right', 'bottom']].astype(dtype).view(
                'f4').reshape((-1, 4)))
        return coords

    @staticmethod
    def get_common(hdr, hdr2):
        d = OrderedDict(**SELECT_ROI_PARAMS['hdr'],
                        **SELECT_ROI_PARAMS['hdr2'])
        common_dtype = np.dtype(dict(names=list(d.keys()),
                                     formats=list(d.values())))
        common = np.zeros(len(hdr), dtype=common_dtype)
        keys = list(SELECT_ROI_PARAMS['hdr'].keys())
        common[keys] = hdr[keys]
        keys2 = list(SELECT_ROI_PARAMS['hdr2'].keys())
        common[keys2] = hdr2[keys2]

        return common

    def _get_points(self, hdr, subpixel):
        # multi-point and individual points not yet implemented,
        # but in the works
        types = [ROI_TYPE['polygon'], ROI_TYPE['freeline'],
                 ROI_TYPE['polyline'], ROI_TYPE['freehand']]
        type_mask = np.isin(hdr['type'], types)
        size = HEADER_SIZE
        coords = [[unpack('>'+n*'f', bs[size+8*n:size+12*n]),
                   unpack('>'+n*'f', bs[size+4*n:size+8*n])]
                  if s else [unpack('>'+n*'h', bs[size+2*n:size+4*n]) + le,
                             unpack('>'+n*'h', bs[size:size+2*n]) + to]
                  for n, to, le, s, bs in zip(hdr['n_coordinates'],
                                              hdr['top'],
                                              hdr['left'],
                                              subpixel,
                                              self.bytestreams)]
        return [(c[0], c[1]) if i else ([], []) for c, i in
                zip(coords, type_mask)]

    def _get_roi_props(self, hdr2_offsets, roi_props_offsets,
                       roi_props_lengths):
        return [''.join(list(map(chr, unpack('>' + 'h'*le, bs[off:off+le*2]))))
                for le, bs, off in zip(
                roi_props_lengths, self.bytestreams, roi_props_offsets)]

    def _get_point_counters(self, offsets, n_coordinates):
        """
        This helps parse a multi-point roi.

        Point counters are ints that encode two parameters: 'positions' and
        'counters'. They describe which c, t, z slice the point roi lies in
        and the index of the point roi in the set, respectively. 'Position'
        is encoded as a short in byte positions 1 and 2, and 'counter' is
        a byte in position 3. Byte 0 is not used.

        Arguments
        -----------
        offset: int
        hdr['counters_offset']

        n_coordinates: int
        hdr['n_coordinates']
        """
        data = [unpack('>'+'hbb'*(n-1) + 'hb', bs[off+1:off+n*4])
                for n, bs, off in zip(
                n_coordinates, self.bytestreams, offsets)]
        positions = [p[::3] for p in data]
        counters = [c[1::3] for c in data]
        return counters, positions

    def cleanup(self):
        try:
            self._file.close()
        except AttributeError:
            pass


class CSVReader(Reader):
    """
    Opens a CSV file and the associated metadata file, converts it to ROI
    format.
    """
    def __init__(self, path, metadata):
        super().__init__()
        self.data = self._read_csv(path)
        self.metadata = self._read_metadata(metadata)

    def _read_csv(self, path):
        # read csv and convert to ROI information
        return NotImplemented

    def _read_metadata(self, md):
        # read json, and return as a nested dictionary
        return NotImplemented
