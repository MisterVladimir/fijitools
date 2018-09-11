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
import os
import re
from addict import Dict

from fijitools.helpers.data_structures import IndexedDict
from fijitools.helpers.iteration import current_and_next


class PathFinder(object):
    """
    Parameters
    -----------
    regexp: str
    Regular expression argument for file name before to extension.

    extension: str
    Extension of desired.
    """
    extension_regexp = {'csv': r'.*\.{1}csv(\.json){0,1}$', 'zip': r'.*.zip$',
                        'tif': r'.*.tiff?$', 'lif': r'.*.lif$'}
    # available_file_formats = {'csv': '.csv', 'zip': '.zip'}

    def __init__(self, regexp=r'.*', extension=None):
        self.extension = extension
        self.regexp = regexp
        self.data = Dict()

    def __getitem__(self, key):
        return self.data[key]

    def load(self, path):
        """
        Returns a list of filenames that match self.regexp and the extension.

        Parameters
        -----------
        path: str
        Folder or file name to load ROI data from.
        """
        # this isn't the most efficient algorithm, as basename filepaths are
        # first globbed, and then matched to the extension's regular expression
        ext = self.extension

        splitpath = path.split(os.path.extsep)
        # path is a file name
        if len(splitpath) > 1:
            folder = os.path.dirname(path)
            if splitpath[-1] == 'csv':
                csv_path, metadata_path = self._get_csv_metadata_path(path)
                filenames = [(csv_path, metadata_path)]
                data_key = 'csv'
            elif splitpath[-1] == 'json' and splitpath[-2] == 'csv':
                csv_path, metadata_path = self._get_csv_metadata_path(
                    "{}".format(os.path.extsep).join(splitpath[:-1]))
                filenames = [(csv_path, metadata_path)]
                data_key = 'csv'

            elif splitpath[-1] == 'zip':
                filenames = [(os.path.basename(path), )]
                data_key = 'zip'

        # path is a directory
        elif ext is not None:
            folder = path
            if ext in ('csv', '.csv'):
                # csv files are a special case because in addition to getting
                # the csv file we must also get the associated metadata,
                # which is in JSON format
                filenames = self._get_csv_filenames(folder)
                data_key = 'csv'
                # return [self._load_csv(*f) for f in filenames]
            elif ext in self.extension_regexp.keys():
                filenames = self._get_filenames(folder, ext)
                data_key = ext

        elif ext is None:
            raise TypeError('Please set extension for folder name arguments.')

        else:
            raise TypeError('File format of {} is not compatible. Please enter'
                            ' a file or path name that contains {}'
                            ' files.'.format(path, list(
                                self.extension_regexp.keys())))

        # add data to self
        if isinstance(self.data[data_key][folder], list):
            self.data[data_key][folder] += filenames
        else:
            self.data[data_key][folder] = []
            self.data[data_key][folder] += filenames

        return filenames

    def _get_csv_metadata_path(self, csv_path):
        """
        Given a CSV file name, find its associated metadata.
        """
        return NotImplemented, NotImplemented

    def _get_csv_filenames(self, folder):
        # TODO: not tested
        # find all CSV files that have metadata
        regexp = re.compile(self.regexp + self.extension_regexp['csv'])
        filenames = [p for p in os.listdir(folder) if regexp.match(p)]
        sorted(filenames)
        li = []
        filenames = iter(filenames)
        n = next(filenames)
        for p in filenames:
            if p == n[:-4]:
                li.append((p, n))
                n = next(filenames)
            elif n == p[:-4]:
                li.append((n, p))
                n = next(filenames)
        return [(csv, next(li)) for csv in iter(li)]

    def _get_filenames(self, folder, extension):
        """
        If it's not a CSV file with metadata, we can default to what is
        basically a glob.glob replacement.
        """
        regexp = re.compile(self.regexp + self.extension_regexp[extension])
        filenames = os.listdir(folder)
        return [(p, ) for p in filenames if regexp.match(p)]


class TiffPathFinder(PathFinder):
    def __init__(self, regexp=r'.*'):
        super().__init__(regexp, 'tif')


class ZipFinder(PathFinder):
    def __init__(self, regexp=r'.*'):
        super().__init__(regexp, 'zip')
