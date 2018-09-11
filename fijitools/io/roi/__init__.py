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
from numpy import dtype
from collections import OrderedDict


# version 1.51
HEADER_SIZE = 64
# version 1.50??? 64 #version 1.51???
HEADER2_SIZE = 52

COLOR_DTYPE = dtype(dict(
    names=['alpha', 'red', 'green', 'blue'],
    offsets=[0, 1, 2, 3],
    formats=['i1', 'i1', 'i1', 'i1']))

HEADER_DTYPE = dtype(dict(
    names=['magic', 'version', 'type', 'top', 'left', 'bottom',
           'right', 'n_coordinates', 'x1', 'y1', 'x2', 'y2',
           'stroke_width', 'shape_roi_size', 'stroke_color',
           'fill_color', 'subtype', 'options', 'arrow_style', 'aspect_ratio',
            # point_type: (0=hybrid, 1=crosshair, 2=dot, 3=circle)
           'point_type', 'arrow_head_size', 'rounded_rect_arc_size',
           'position', 'hdr2_offset'],
    offsets=[0, 4, 6, 8, 10, 12,
             14, 16, 18, 22, 26, 30,
             34, 36, 40,
             44, 48, 50, 52, 52,
             52, 53, 54,
             56, 60],
    formats=[(bytes, 4), '>i2', '<i2', '>i2', '>i2', '>i2',
             '>i2', '>i2', '>f4', '>f4', '>f4', '>f4',
             '>i2', '>i2', COLOR_DTYPE,
             COLOR_DTYPE, '>i2', '>i2', 'i1', '>f4',
             'i1', 'i1', '>i2',
             '>i4', '>i4']))

HEADER2_DTYPE = dtype(dict(
    names=['c', 'z', 't', 'name_offset', 'name_length', 'overlay_label_color',
           'overlay_font_size', 'image_opacity', 'image_size',
           'float_stroke_width', 'roi_props_offset', 'roi_props_length',
           'counters_offset'],
    offsets=[4, 8, 12, 16, 20, 24,
             28, 31, 32,
             36, 40, 44,
             48],
    formats=['>i4', '>i4', '>i4', '>i4', '>i4', '>i4',
             '>i2', 'i1', '>i4',
             '>f4', '>i4', '>i4',
             '>i4']))

OPTIONS = {'spline_fit': 1,
           'double_headed': 2,
           'outline': 4,
           'overlay_labels': 8,
           'overlay_names': 16,
           'overlay_backgrounds': 32,
           'overlay_bold': 64,
           'subpixel': 128,
           'draw_offset': 256,
           'zero_transparent': 512}

SUBTYPE = {'text': 1,
           'arrow': 2,
           'ellipse': 3,
           'image': 4,
           'rounded_rectangle': 5}

ROI_TYPE = {'polygon': 0,
            'rectangle': 1,
            'oval': 2,
            'line': 3,
            'freeline': 4,
            'polyline': 5,
            'no_roi': 6,
            'freehand': 7,
            'traced': 8,
            'angle': 9,
            'point': 10}

SELECT_ROI_PARAMS = {'hdr': OrderedDict([('magic', (bytes, 4)),
                                         ('version', 'i2'),
                                         ('type', 'i2'),
                                         ('stroke_width', 'i2'),
                                         ('stroke_color', COLOR_DTYPE),
                                         ('fill_color', COLOR_DTYPE),
                                         ('subtype', 'i2'),
                                         ('options', 'i2'),
                                         ('aspect_ratio', 'f4'),
                                         ('point_type', 'i1'),
                                         ('hdr2_offset', 'i4')]),
                     'hdr2': OrderedDict([('c', 'i4'),
                                          ('z', 'i4'),
                                          ('t', 'i4'),
                                          ('float_stroke_width', 'f4'),
                                          ('roi_props_offset', 'i4'),
                                          ('roi_props_length', 'i4'),
                                          ('counters_offset', 'i4')])}
