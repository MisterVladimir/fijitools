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
import unittest

from fijitools.io.roi import roi_read


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def run_tests(*test_classes):
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)
    for class_ in test_classes:
        loaded_tests = loader.loadTestsFromTestCase(class_)
        runner.run(loaded_tests)


class AbstractTestClass(ABC):
    roi_path = None
    h5_path = None

    def setUp(self):
        """Load ROI data from ZIP file"""
        # to overcome error in
        if self.roi_path is not None:
            with roi_read.IJZipReader(sep='-') as f:
                self.zipname = os.path.splitext(os.path.basename(self.roi_path))[0]
                f.read(self.roi_path, name=self.zipname)
                self.data = f.data
