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
import csv
import re
from pandas import read_csv
from abc import ABC, abstractmethod


class HeaderGetter(ABC):
    """
    HeaderGetter is parent class of all csv file-reading objects. HeaderGetter
    does not actually import any data, but stores only the csv file's header
    information. This class helps avoid reading in an entire csv file just to grab and filter the
    header information.

    Parameters
    ------------
    filepath : str
        Path to the csv file.

    header_row : int
        Row number of header. Index starts at zero.

    Attributes
    ------------
    header : str
        Header of csv file.

    header_row: int
        Row number of the csv's header set by the user. Most csv file's
        headers are the first (zeroth) row.

    Methods
    ------------
    get_row
        Returns the values of a single row in a csv file. 
    """

    def __init__(self, filepath, header_row=0):
        self.filepath = filepath
        self.header_row = header_row
        self.header = self.get_row(filepath, header_row)
        self.get_data()

    def get_row(self, fp, rw):
        """ 
        http://stackoverflow.com/questions/24962908/how-can-i-read-only-the-header-column-of-a-csv-file-using-python

        If header_row == 0, this is easy; just get the fieldnames (first row).
        Otherwise, call DictReader.next() until we get to the correct row, and
        read in that row as the headers.

        Parameters
        ----------
        fp: str
        *.csv file name. 

        rw : int
            Row number whose values you want to return as strings.
        """
        with open(fp, 'rb') as input_file:
            reader = csv.DictReader(input_file)
            if rw is 0:
                return reader.fieldnames
            elif rw is None:
                # For example, JFilament CSVs don't have a header to determine
                # X and Y coordinates. Use None to extract columns by number.
                return None
            else:
                # iterating through rows until you get to the right one
                counter = 2
                for row in reader:
                    if counter == rw:
                        # self.header_row = counter
                        return row.values()
                    counter += 1

    @abstractmethod
    def get_data(self):
        raise NotImplementedError()

    @abstractmethod
    def write_data(self, filepath):
        raise NotImplementedError()


class FilteredCSV(HeaderGetter):
    """
    """
    def __init__(self, filepath, measurements=None, header_row=0):
        """
        Parameters
        ----------
        filepath : str

        measurements : list of str
            Measurements we want to extract, e.g. 'Mean'.
            Uses re library wildcards. We do this because Fiji's Multi Measure
            function creates a Results table in which columns concatenate the
            ROI number with the measurement type. For example, if we drew two
            ROI, and checked "Mean" and "Max" in Fiji's "Set Measurements",
            the column names would be "Mean1", "Max1", "Mean2", "Max2". To get
            the Mean columns, enter measurements='Mean*'.

            Note: if we want to match the pattern exactly, we must
            anchor the pattern. e.g. re.match('X', 'XM') would return a Match
            object but re.match('X$', 'XM') would not. That is, 'X' matches
            'XM' but 'X$' does not.
        """
        super().__init__(filepath, header_row)
        self.measurements = measurements
        if self.header is not None:
            self.filter_header(measurements)

    def get_data(self):
        self.data = read_csv(self.filepath, header=self.header_row,
                             usecols=self.header)

    def filter_header(self, measurements):
        h = [h for h in self.header for me in measurements if re.match(me, h)]
        self.header = np.unique(h)

    def write_data(self, filepath):
        self.data.to_csv(filepath)


class FloatCSV(FilteredCSV):
    """
    Reads all rows as np.float32.
    """

    def __init__(self, filepath, measurements):
        super().__init__(filepath, measurements)

    def get_data(self):
        return read_csv(self.filepath, engine='c', dtype=np.float32,
                        usecols=self.header)
