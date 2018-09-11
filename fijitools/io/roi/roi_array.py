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
import copy

from endocytosis.helpers.coordinate import Coordinate


class RoiArray(object):
    pass


# not teseted
class EndocytosisRoiSet(RoiArray):
    """
    Crude center of mass-based method for adding ROI to an exising
    set of ROI capturing an endocytic event over time.
    """
    def augment(self, imreader, lower=0, upper=0):
        def center_of_mass(arr, X, Y):
            # center of mass
            arrsum = arr.sum()
            return np.array([(arr*X).sum()/arrsum,
                             (arr*Y).sum()/arrsum])
        if not lower == 0:
            roi = copy.copy(self[0])
            c, t, z = roi.c, roi.t, roi.z
            roi.sides += Coordinate(px=(4, 4))
            xsl, ysl = roi.to_slice()
            dx, dy = roi.sides['px'].astype(int)
            X, Y = np.mgrid[:dx, :dy]
            for _t in range(t-1, t-lower-1, -1):
                imdata = imreader.data.request(c, _t, z, xsl, ysl)
                com = Coordinate(px=center_of_mass(imdata, X, Y))
                origin = list(com['px'])
                bottom_right = list(origin + roi.sides['px'])
                arg = origin + bottom_right + [c, _t, z]
                self.insert(0, self.roi_class(arg, None))