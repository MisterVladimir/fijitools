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

import unittest
import os
from test import AbstractTestClass

from fijitools.io.roi import (roi_write, roi_read)


class WriteTest(AbstractTestClass):
    def test_write_one(self):
        roi = self.data[self.zipname]['item']['0']
        with roi_write.Hdf5Writer(self.h5_path) as w:
            w.write(roi, ('t', 'c', 'centroid'), 'im', 'centroid')

    def tearDown(self):
        try:
            os.remove(self.h5_path)
        except OSError:
            print("There was an error while attempting to remove {}.".format(
                  self.h5_path))


class RectWriteTest(WriteTest, unittest.TestCase):
    roi_path = WriteTest.as_path('rectangles.zip')
    h5_path = WriteTest.as_path('rectangles.h5')


class OvalWriteTest(WriteTest, unittest.TestCase):
    roi_path = WriteTest.as_path('ovals.zip')
    h5_path = WriteTest.as_path('ovals.h5')


if __name__ == '__main__':
    test_classes = (RectWriteTest, OvalWriteTest)
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)
    for class_ in test_classes:
        loaded_tests = loader.loadTestsFromTestCase(class_)
        runner.run(loaded_tests)
