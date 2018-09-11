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
from struct import pack
from collections import OrderedDict
import warnings
from abc import ABC, abstractmethod
from PyQt5.QtGui import (QFont, QFontMetrics)

from fijitools.helpers.iteration import current_and_next
from fijitools.helpers.coordinate import Coordinate
from fijitools.helpers.data_structures import RoiPropsDict
from fijitools.helpers.iteration import isiterable
from fijitools.io.roi import (HEADER_SIZE, HEADER2_SIZE,
                              HEADER_DTYPE, HEADER2_DTYPE,
                              OPTIONS, SUBTYPE, ROI_TYPE,
                              COLOR_DTYPE, SELECT_ROI_PARAMS)


# TODO: store ROI coordinates in physical units e.g. nanometers instead
# of pixels
# TODO: latest version not tested

class BaseROI(ABC):
    # implement in child classes
    roi_type = None
    compatible_roi = []
    skipped_fields = {'hdr': [], 'hdr2': []}

    def __init__(self, common, props, from_ImageJ=True):
        # populate properties common to all ROI into a numpy array
        # this makes it convenient to later export self as an ImageJ bytestream
        if from_ImageJ:
            # loaded with roi_read.IJZipReader, already formated
            self.select_params = common
        elif isinstance(common, dict):
            d = OrderedDict(**SELECT_ROI_PARAMS['hdr'],
                            **SELECT_ROI_PARAMS['hdr2'])
            dtype = np.dtype(dict(names=list(d.keys()),
                                  formats=list(d.values())))
            self.select_params = np.zeros(1, dtype)
            for k, v in common.items():
                if k in self.select_params.names:
                    if isiterable(v):
                        self.select_params[k] = tuple(v)
                    else:
                        self.select_params[k] = v

            for k, v in [('magic', b'Iout'), ('version', 227),
                         ('type', ROI_TYPE[self.roi_type])]:
                self.select_params[k] = v

        self.roi_props = props
        # self._top_left = None
        # self._sides = None
        # self._pixelsize = None

    def _set_bounding_rect(self, br):
        # ensures that origin is top left corner of the rectangle
        top_left = np.minimum(br[:2], br[2:], dtype='f4')
        bottom_right = np.maximum(br[:2], br[2:], dtype='f4')
        sides = bottom_right - top_left
        self._top_left = Coordinate(px=top_left)
        self._sides = Coordinate(px=sides)

    @property
    def top_left(self):
        return self._top_left

    @top_left.setter
    def top_left(self, value):
        assert isinstance(value, Coordinate)
        self._top_left = value

    @property
    def sides(self):
        return self._sides

    @sides.setter
    def sides(self, value):
        # change self.top_left to maintain the bounding rectangle's center
        assert isinstance(value, Coordinate)
        self._sides = value
        self._top_left -= value

    @property
    def centroid(self):
        return self._top_left + self._sides / 2

    def _encode_points(self):
        raise NotImplementedError('')

    @property
    def points(self):
        raise NotImplementedError('')

    @points.setter
    def points(self, value):
        raise NotImplementedError('')

    @property
    def roi_props(self):
        return self._roi_props

    @roi_props.setter
    def roi_props(self, value):
        if isinstance(value, (str, bytes)):
            self._roi_props = RoiPropsDict(string=str(value))
        elif isinstance(value, dict):
            self._roi_props = RoiPropsDict(**value)
        else:
            raise TypeError('roi_props may only be set with a string, bytes'
                            'or dictionary.')

    @property
    def ctz(self):
        return self.select_params[0][['c', 't', 'z']]

    @property
    def c(self):
        return self.ctz['c']

    @property
    def t(self):
        return self.ctz['t']

    @property
    def z(self):
        return self.ctz['z']

    @property
    def subpixel(self):
        return self.select_params['options'] & OPTIONS['subpixel']

    @property
    def options(self):
        return self.select_params['options']

    def _set_color(self, key, value):
        if isinstance(value, dict):
            for k, v in value.items():
                self.select_params[key][k] = str(v)
        elif isiterable(value) and len(value) == 4:
            self.select_params[key] = tuple(value)

    @property
    def fill_color(self):
        # a, r, g, b format
        return self.select_params['fill_color'][0]

    @fill_color.setter
    def fill_color(self, value):
        self._set_color('fill_color', value)

    @property
    def stroke_color(self):
        # a, r, g, b format
        return self.select_params['stroke_color'][0]

    @stroke_color.setter
    def stroke_color(self, value):
        self._set_color('stroke_color', value)

    @property
    def stroke_width(self):
        if self.subpixel:
            return self.select_params['float_stroke_with']
        else:
            return self.select_params['stroke_with']

    @stroke_width.setter
    def stroke_width(self, value):
        if self.subpixel:
            self.select_params['float_stroke_with'] = float(value)
        self.select_params['stroke_with'] = np.int16(value)

    @property
    def pixelsize(self):
        try:
            return self.roi_props['pixelsize']
        except KeyError:
            return None

    @pixelsize.setter
    def pixelsize(self, c):
        # if pixelsize has already been set once, 
        # setting a new value will raise an AttributeError
        # from self._top_left and self._sides
        if not self._top_left.pixelsize == c:
            # avoids attribute error
            self._top_left.pixelsize = c
        else:
            self._sides.pixelsize = c
        self.roi_props['pixelsize'] = c

    def to_slice(self):
        x0, y0 = self._top_left['px'].astype(int)
        dx, dy = self._sides['px'].astype(int)
        return [slice(x0, x0 + dx), slice(y0, y0 + dy)]

    @staticmethod
    def _encode_name(name):
        """
        """
        name = list(map(ord, list(name)))
        return pack('>' + 'h'*len(name), *name)

    @abstractmethod
    def _encode_points(self):
        pass

    @classmethod
    def to_IJ(cls, roi, name, image_name=''):
        """
        Organizes ROI information common to all ROI types. Child classes
        should () methods to ()

        Arguments
        -----------
        roi: BaseROI
        Any concrete child class of BaseROI.

        name: str
        Name of the ROI.

        image_name: str (optional)
        Image name to be written into roi_props.

        Returns
        -----------
        hdr: numpy.ndarray
        dtype is HEADER_DTYPE.

        hdr2: numpy.ndarray
        dtype is HEADER2_DTYPE.

        encoded_roi_name: bytes[]
        ROI name, encoded as big endian shorts.

        roi_props: fijitools.helpers.data_structures.RoiPropsDict
        ROI properties associated with roi.

        """
        hdr = np.zeros(1, dtype=HEADER_DTYPE)
        hdr2 = np.zeros(1, dtype=HEADER2_DTYPE)

        # hdr data
        keys = list(SELECT_ROI_PARAMS['hdr'].keys())
        hdr[keys] = roi.select_params[keys]
        try:
            hdr['hdr2_offset'] = HEADER_SIZE + 4 + \
                len(roi.points)*(4+8*int(roi.subpixel))
        except NotImplementedError:
            hdr['hdr2_offset'] = HEADER_SIZE + 4

        x0, y0 = roi.top_left['px']
        x1, y1 = (roi.top_left + roi.sides)['px']
        coords = (y0, x0, y1, x1)
        if roi.subpixel:
            hdr[['x1', 'y1', 'x2', 'y2']] = coords
        hdr[['top', 'left', 'bottom', 'right']] = tuple(map(int, coords))

        # hdr2 data
        keys2 = list(SELECT_ROI_PARAMS['hdr2'].keys())
        hdr2[keys2] = roi.select_params[keys2]

        # name is stored as shorts
        encoded_name = cls._encode_name(name)
        hdr2['name_offset'] = hdr['hdr2_offset'] + HEADER2_SIZE
        hdr2['name_length'] = len(encoded_name)//2

        # set roi properties (text at the end of .roi file)
        roi_props = roi.roi_props.to_IJ(image_name)
        hdr2['roi_props_offset'] = hdr['hdr2_offset'] + HEADER2_SIZE + \
            len(encoded_name)
        hdr2['roi_props_length'] = len(roi_props)

        if roi.__class__ == cls:
            pass
        elif roi.roi_type in cls.compatible_roi or \
                SUBTYPE[roi.select_params['subtype']] in cls.compatible_roi:
            hdr[cls.skipped_fields['hdr']] = 0
            hdr2[cls.skipped_fields['hdr2']] = 0
            hdr['type'] = ROI_TYPE[cls.roi_type]
            if roi.subpixel:
                hdr2['subtype'] = SUBTYPE['ellipse']
        else:
            raise TypeError("{} is not compatible with {}'s to_IJ() "
                            "method.".format(roi.__class__, cls))

        encoded_points = roi._encode_points()

        return (hdr.tobytes() + encoded_points + b'\x00\x00\x00\x00' +
                hdr2.tobytes() + encoded_name + roi_props)

    def to_nested_dict(self, attrs, *args):
        """
        Generates a nested dictionary which can be easily put into an hdf5
        file.

        Arguments
        ----------
        attrs: iterable containing strings
        ROI properties.

        args: iterable containing strings
        Additional dictionary keys to precede

        Results in something like {image_name: {attribute_name: {roi_name: {t: attribute value}}}}
        """
        last = getattr(self, attrs[-1])
        if isinstance(last, Coordinate):
            last = last['px']
        for attr in reversed(attrs[:-1]):
            ret = {}
            key = str(getattr(self, attr))
            ret[key] = last
            last = copy.copy(ret)
        for arg in reversed(args):
            ret = {}
            ret[arg] = last
            last = copy.copy(ret)

        return ret


class TextROI(BaseROI):
    roi_type = 'rectangle'

    def __init__(self, text, topleft, font_size, c, t, z, font_name='Courier'):
        super().__init__({'c': c, 't': t, 'z': z, 'subtype': SUBTYPE['text']},
                         RoiPropsDict(), False)
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self._set_bounding_rect(text, topleft, font_name, font_size)

    def _set_bounding_rect(self, text, top_left, font_name, font_size):
        font = QFont(font_name, font_size)
        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(text)
        height = metrics.height()
        # ensures that origin is top left corner of the rectangle
        self._top_left = Coordinate(px=top_left)
        self._sides = Coordinate(px=[width, height])

    def _encode_points(self):
        # for text roi, the bytes between hdr and hdr2 are the text properties,
        # not any coordinates
        dtype = [('size', '>i4'), ('style', '>i4'), ('font_name_length', '>i4')
                 ('text_length', '>i4')]
        arr = np.zeros(1, dtype)
        arr['size'] = self.font_size
        arr['font_name_length'] = len(self.font_name)
        arr['text_length'] = len(self.text)
        encoded_font_name = self._encode_name(self.font_name)
        encoded_text = self._encode_name(self.text)
        ret = arr.tobytes() + encoded_font_name + encoded_text + \
            b'\x00\x00\x00\x00'
        self.select_params['hdr2_offset'] = HEADER_SIZE + len(ret)
        return ret

    @property
    def points(self):
        pass

    @points.setter
    def points(self, value):
        pass


class NonTextROI(BaseROI):
    """
    ImageJ's text ROI has a very different format from other ROI types, so
    they deserve their own parent class.
    """
    pass


class RectROI(NonTextROI):
    """
    Parameters
    -----------
    props: string or RoiProps
    """
    roi_type = 'rectangle'
    skipped_fields = {'hdr': ['shape_roi_size', 'subtype', 'arrow_style',
                              'aspect_ratio', 'point_type', 'arrow_head_size',
                              'rounded_rect_arc_size', 'position'],
                      'hdr2': ['overlay_label_color', 'overlay_font_size',
                               'image_opacity', 'image_size',
                               'float_stroke_width']}
    compatible_roi = ['oval', 'ellipse']

    def __init__(self, bounding_rect, common, props='', from_ImageJ=True,
                 **kwargs):
        super().__init__(common, props, from_ImageJ)
        self._set_bounding_rect(bounding_rect)

    def _encode_points(self):
        return b''


class PointContainingROI(NonTextROI):
    """
    Abstract base class for ellipse, polygon, polyline, etc.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._points = None

    def _update_bounding_rect(self):
        pts = np.array([c['px'] for c in self._points])
        top_left = pts.min(axis=0)
        sides = pts.max(axis=0) - top_left
        self._top_left = Coordinate(px=top_left)
        self._sides = Coordinate(px=sides)

    def _set_points(self, pts):
        def rollback():
            self._points = old_points

        old_points = copy.copy(self._points)
        self._points = [Coordinate(**c) if isinstance(c, Coordinate)
                        else Coordinate(px=c) for c in pts]
        ps = filter(lambda x: getattr(x, 'pixelsize'), self._points)

        try:
            prev = next(ps)
        except StopIteration:
            # empty iterator -> no pixelsizes set in self._points
            pass
        else:
            # make sure all points whose pixelsize property is not None
            # have the same pixelsize
            for p in ps:
                if not p == prev:
                    rollback()
                    raise AttributeError('Not all pixelsizes in self._points '
                                         'are equal. Rolling back.')
                prev = p

            try:
                # also sets pixelsizes of every element in self._points
                self.pixelsize = prev
            except AttributeError as e:
                rollback()
                raise AttributeError('Cannot set pixelsize from self._points.'
                                     'Rolling back') from e


# not tested
class EllipseROI(PointContainingROI):
    """

    kwargs
    -------
    Must contain one of the following sets:
    x1, y1, x2, y2, d: two centroid coordinates and diameter
    aspect_ratio, width, height, (x0, y0) or (xc, yc):
    xc, yc, a, b, theta: centroid coordinates, axis lengths and angle

    """
    roi_type = None
    skipped_fields = {'hdr': ['shape_roi_size', 'arrow_style', 'point_type',
                              'arrow_head_size', 'rounded_rect_arc_size',
                              'position'],
                      'hdr2': ['overlay_label_color', 'overlay_font_size',
                               'image_opacity', 'image_size',
                               'float_stroke_width']}
    compatible_roi = []

    def __init__(self, common, props='', from_ImageJ=True, **kwargs):
        super().__init__(common, props, from_ImageJ)
        # self.select_params['subtype'] = SUBTYPE['ellipse']
        # default setting from imageJ
        self.vertices = 72
        if self.subpixel:
            self.roi_type = 'freehand'
        else:
            self.roi_type = 'oval'

        if from_ImageJ:
            self._set_bounding_rect(kwargs['bounding_rect'])
            if self.subpixel:
                self._set_points(kwargs['points'])
                ratio = self.sides['px'] / np.roll(self.sides['px'], 1)
                # aspect ratio = minor / major length
                self.aspect_ratio = np.min(ratio)

        if 'points' in kwargs.keys() and any(kwargs['points']):
            self._set_points(kwargs['points'])
            self._update_bounding_rect()
            self._calculate_aspect_ratio()

        else:
            if self.select_params['aspect_ratio']:
                kwargs['aspect_ratio'] = self.select_params['aspect_ratio']
            # determine whether it's x0, y0 or xc, yc
            self._calculate_points(**kwargs)

    def _encode_points(self):
        if self.subpixel:
            raise NotImplementedError('')
        else:
            return b''

    def _calculate_points(self, **kwargs):
        # untested
        # for calculating points from bounding rectangle + aspect ratio
        beta1 = np.array([2*i*np.pi/self.vertices for
                          i in range(self.vertices)])
        major = np.hypot(*self.sides['px'])
        minor = self.aspect_ratio*major
        dx = np.sin(beta1) * major / 2.0
        dy = np.cos(beta1) * minor / 2.0
        beta2 = np.arctan2(dx, dy)
        rad = np.hypot(dx, dy)
        beta3 = beta2 + self.angle / 180.0 * np.pi
        dx2 = np.sin(beta3)*rad
        dy2 = np.cos(beta3)*rad
        points = self.centroid['px'][None, :] + np.array([dx2, dy2]).T
        if self.pixelsize:
            return [Coordinate(px=p, nm=p*self.pixelsize) for p in points]
        else:
            return [Coordinate(px=p) for p in points]

    @property
    def points(self):
        if self.subpixel:
            return self._points
        else:
            raise NotImplementedError('')

    @property
    def angle(self):
        # not sure if this is correct
        return np.arctan2(*self.sides['px']) * 180.0 / np.pi

    @property
    def aspect_ratio(self):
        return self.select_params['aspect_ratio']

    def _calculate_aspect_ratio(self):
        """
        Calculate aspect ratio from...
        """
        pass

    @aspect_ratio.setter
    def aspect_ratio(self, value):
        self.select_params['aspect_ratio'] = value


class PolygonROI(PointContainingROI):
    roi_type = 'polygon'

    def __init__(self, common, points, props='', from_ImageJ=True, **kwargs):
        super().__init__(common, props, from_ImageJ)
        if from_ImageJ:
            points = self._adjust_ImageJ_points(points, 
                                                kwargs['bounding_rect'])
        self._set_points(points)
        if 'bounding_rect' in kwargs.keys():
            self._set_bounding_rect(kwargs['bounding_rect'])
        else:
            self._update_bounding_rect()

    def _adjust_ImageJ_points(self, pts, bounding_rect):
        """
        If ImageJ ROI is not subpixel, its points are stored relative to the
        top left corner's coordinates. Here we adjust them to be relative
        to the image's top left corner.
        """
        if self.subpixel:
            return pts
        else:
            return pts + bounding_rect[:2].astype(int)

    def _encode_points(self):
        arr = np.array([p['px'] for p in self._points])
        if self.subpixel:
            arr_sub = arr
        else:
            arr_sub = np.zeros_like(arr)
        arr_nonsub = (arr - self._top_left['px']).astype(np.int16)
        return arr_sub.tobytes('F') + arr_nonsub.tobytes('F')

    @property
    def top_left(self):
        return self._top_left

    @property
    def sides(self):
        return self._sides

    @property
    def points(self):
        try:
            return self._points
        except AttributeError:
            return None

    @property
    def pixelsize(self):
        return self.roi_props['pixelsize']

    @pixelsize.setter
    def pixelsize(self, c):
        if not self._top_left.pixelsize == c:
            # avoids attribute error
            self._top_left.pixelsize = c

        if not self._sides.pixelsize == c:
            self._sides.pixelsize = c

        for p in self._points:
            if not p.pixelsize == c:
                p.pixelsize = c

        self.roi_props['pixelsize'] = c

    @property
    def spline_fit(self):
        return False


class PolyLineROI(PolygonROI):
    roi_type = 'polyline'

    @property
    def spline_fit(self):
        return bool(self.select_params['options'] & OPTIONS['spline_fit'])

    @spline_fit.setter
    def spline_fit(self, b):
        if b:
            self.select_params['options'] = \
                self.select_params['options'] | OPTIONS['spline_fit']
        else:
            self.select_params['options'] = \
                self.select_params['options'] & ~OPTIONS['spline_fit']


class FreeLineROI(PolygonROI):
    roi_type = 'freeline'


def ROI(bounding_rect, common, points, props, typ, from_ImageJ=True):
    """
    Factory function for generating ROI from ImageJ data.
    """
    number_to_roi_class = {ROI_TYPE['rectangle']: RectROI,
                           ROI_TYPE['oval']: EllipseROI,
                           ROI_TYPE['polygon']: PolygonROI,
                           ROI_TYPE['freeline']: FreeLineROI,
                           ROI_TYPE['polyline']: PolyLineROI,
                           ROI_TYPE['freehand']: FreeLineROI}
    if common['subtype'] == SUBTYPE['ellipse']:
        return EllipseROI(common=common, props=props, from_ImageJ=from_ImageJ,
                          bounding_rect=bounding_rect, points=points)
    elif common['subtype'] == SUBTYPE['text']:
        return TextROI(common=common, props=props, from_ImageJ=from_ImageJ, 
                       bounding_rect=bounding_rect, points=points)
    else:
        cls_ = number_to_roi_class[typ]
        return cls_(common=common, props=props, from_ImageJ=from_ImageJ, 
                    bounding_rect=bounding_rect, points=points)
