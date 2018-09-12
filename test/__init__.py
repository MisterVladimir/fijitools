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
from abc import ABC
import os

from fijitools.io.roi import roi_read


class AbstractTestClass(ABC):
    roi_path = NotImplemented
    h5_path = NotImplemented

    def setUp(self):
        # load ROI data from ZIP file
        with roi_read.IJZipReader(sep='-') as f:
            self.zipname = os.path.splitext(os.path.basename(self.roi_path))[0]
            f.read(self.roi_path, name=self.zipname)
            self.data = f.data

    @staticmethod
    def as_path(name):
        return os.path.abspath(os.path.join(
            os.path.curdir, 'test', 'data', name))
