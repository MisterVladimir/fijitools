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
import scipy.ndimage as ndi
from scipy.interpolate import splrep, splev
# from skimage.morphology import disk
from numpy.lib.stride_tricks import as_strided
from skimage.measure import EllipseModel
# from scipy.integrate import quad


# very old partially-tested code
class BaseROI(object):
    def _set_bounding_box(self):
        x_min, y_min = self.points.min(0)
        x_max, y_max = self.points.max(0)
        self._bounding_box = np.array([[x_min, y_min], 
                                       [x_max, y_min], 
                                       [x_min, y_max],
                                       [x_max, y_max]])

    def bounding_box(self, pad):
        """Coordinates of the bounding box corners."""
        pad = np.array([[-pad, -pad],
                        [ pad, -pad],
                        [-pad,  pad],
                        [ pad,  pad]])
        return self._bounding_box + pad

    def as_slice(self, pad=0):
        """Returns rectangular ROI as slice object"""
        bb = self.bounding_box(pad).astype(int)
        x_min, y_min = bb[0]
        x_max, y_max = bb[3]
        return [slice(x_min, x_max+1), slice(y_min, y_max+1)]

    def masker(self, pad=0):
        """
        For masking images.
        
        Returns 
        --------
        A masking function whose parameter is the image to be masked. This 
        function, in turn, returns the pixels of this ROI. 
        """
        xsl, ysl = self.as_slice(pad)
        bb = self.bounding_box(pad)
        x, y = (self.points - bb[0]).T.astype(int)
        mask = np.zeros((xsl.stop-xsl.start, 
                         ysl.stop-ysl.start), dtype=bool)
        mask[x, y] = True
        if self.filled: 
            mask = ndi.binary_fill_holes(mask)
        return lambda im: im[[xsl, ysl]]*mask


class RectROI(BaseROI):
    """
    Initialized with either an 4x2 numpy.ndarray containing the coordinates of
    the four corners or with 2x2 numpy.ndarray of two corners.
    """
    filled = True
    def __init__(self, points):
        self.points = points

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, p):
        try:
            x = p.x
            y = p.y
            self._points = np.asarray([x, y]).T
        except AttributeError:
            if isinstance(p, tuple):
                raise TypeError("x, y, half_width input parameters not yet"
                                "implemented.")
            elif p.shape == (2, 2):
                # two corners
                x = p[0]
                y = p[1]
                self._points = np.asarray([[x[0], x[1], x[0], x[1]],
                                           [y[0], y[0], y[1], y[1]]]).T
            elif p.shape == (4, 2):
                # four corners
                self._points = np.asarray(p)
            else: 
                raise TypeError("Something went wrong.")


class PointROI(RectROI):
    filled = False
    def __init__(self, point):
        self.points = point

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, p):
        assert(len(p) == 2)
        self._points = np.atleast_2d(p)

    def to_square(self, s):
        """
        Parameters
        s : int
            Side length, in pixels.
        """
        self.s = s
        self._set_bounding_box()
        self._bounding_box = self.bounding_box(s/2)
        self.filled = True
    
    def integrated_density(self):
        try: 
            bb = self._bounding_box[[0, 3]].T.ravel()
        except AttributeError:
            print("Returning None. Please set square side length first.")
            return None
        else: 
            return lambda rbs: rbs.integral(*bb)
        

class SegmentedROI(BaseROI): 
    """
    Currently includes polygon, polyline, line.
    """
    def _spline(self, points, **kwargs):
        """
        Interpolates xy Nx2 array at 0.5 pixel intervals using B splines
        https://stackoverflow.com/questions/19117660/how-to-generate-equispaced-interpolating-values
        """ 
        x, y = points.T
        try: 
            if kwargs['per']:
                # force periodicity 
                if not np.isclose(x[0], x[-1]):
                    x = np.append(x, x[0])
                if not np.isclose(y[0], y[-1]):
                    y = np.append(y, y[0])
        except KeyError:
            if x[0] == x[-1] and y[0] == y[-1]:
                kwargs['per'] = True
            else:
                kwargs['per'] = False
        self.periodic = kwargs['per']
        # m = number of points is a function of the total length
        # m = int(sum([np.hypot(*(cur-nex)) for cur, nex in current_and_next(
        #                                                               points)]))
        m = 1001
        t = np.linspace(0, len(x)-1, m, endpoint=True)
        x = splev(t, splrep(np.arange(len(x)), x, **kwargs))
        y = splev(t, splrep(np.arange(len(y)), y, **kwargs))
        xy = np.concatenate((x, y)).reshape((-1, 2), order='F')

        # TODO: improve performance with np.cumsum and as_strided
        tol, dist, ind = 0.5, 0., [0]
        for i, c in enumerate(current_and_next(xy)):
            dist += np.hypot(*(c[1]-c[0]))
            if dist > tol:
                ind.append(i)
                dist = 0.
        return np.stack([x[ind], y[ind]]).T

class PolygonROI(SegmentedROI): 
    filled = True
    def __init__(self, points): 
        """
        points : numpy.ndarray 
            Nx2 array of x, y coordinates in pixels. 
        """
#        if periodic: 
#            while np.hypot(*[np.ediff1d(r) for r in points.T]).max() > 0.5: 
#                points = self._bulge(points) 
        kwargs = {'k': 1, 'per': True}
        self.points = self._spline(points, **kwargs)
        self._set_bounding_box()
    
    @property
    def center(self): 
        return self.points.mean(0)

class PolylineROI(SegmentedROI): 
    filled = False
    def __init__(self, points, periodic='infer'): 
        """
        points : numpy.ndarray 
            Nx2 array of x, y coordinates in pixels. 
        """
#        if periodic: 
#            while np.hypot(*[np.ediff1d(r) for r in points.T]).max() > 0.5: 
#                points = self._bulge(points) 
        kwargs = {'k':3}
        if isinstance(periodic, bool): 
            kwargs['per'] = periodic
        self.points = self._spline(points, **kwargs)
        self._set_bounding_box()

    def _bulge(self, points): 
        """
        Alternative to _spline.
        
        https://www.cc.gatech.edu/~ghost/classes/2007fall/cs6491/lecture1/
        
        Note that unlike self._spline, this doesn't attempt even spacing 
        between points
        """
        s = points.shape[0]
        L = np.stack([points.take(range(i, i+s), axis=0, mode='wrap') for i in [0,1]]).mean(0)
        K = np.stack([points.take(range(i, i+s), axis=0, mode='wrap') for i in [-1,0]]).mean(0)
        M = np.stack([points.take(range(i, i+s), axis=0, mode='wrap') for i in [1,2]]).mean(0)
        X = (K + M)/2
        ret = np.zeros((s*2, 2))
        ret[::2] = points
        ret[1::2] = L + (L-X)/4
        return ret
            
    def _check_thickness(self, thickness): 
        """
        What is the most this one-dimensional ROI can be widened? 
                
        First, calculate the curvature at each point along the ROI. The 
        maximum value of the inverse curvature (radius) is the maximum 
        thickness that can be accomodated by the ROI. 
        
        Thanks to Rui Ma for suggesting this method. 
        """
#        curvature along array = 4*area / product of three sides of the triangle
        points = self.points
        a = np.hypot(*points[:,1:-1]-points[:, :-2]) # side lengths of triangle
        b = np.hypot(*points[:,2:  ]-points[:,1:-1])
        c = np.hypot(*points[:, :-2]-points[:,2:  ])
#        heron's forumla to calculate area 
        p = (a + b + c)/2.
        area = np.sqrt(p*(p-a)*(p-b)*(p-c))
#        obtain the radius: placing area as numerator and taking reciprocal 
#        overcomes potential zero values in "triangle" areas
        max_radius = 1./(4.*area / (a*b*c)).max() # 1/curvature
        if thickness > max_radius: 
            print('Thickness too high; using maximum allowed thickness.')
            self.thickness = max_radius
        else: 
            self.thickness = thickness
            
        return self.thickness
        
    def _intensity_prep(self, thickness): 
        """
        Creates a meshgrid along the thickened line, and calculates the 
        centroid and area of each grid location. 
        """
        if thickness == 0: 
            self.cx, self.cy = self.points.T
            self.areas = np.ones_like(self.cx)[:,None]
            return None
        
        if self.periodic: 
            points = np.concatenate((self.points[-1][None,:], 
                                     self.points, 
                                     self.points[0][None,:]
                                     )
                                    ) 
#            slope at a point is average slope between points on either side  
            m = np.gradient(points, axis=0)[1:-1]
            points = points[1:-1]
#            m = points[:,2:] - points[:,:-2]
        else: 
            points = self.points
            m = np.gradient(points, axis=0)
#        get unit vector slope, take negative reciprocal to get perpendicular slope 
        m = [[-1.], [1.]]*np.roll(m/np.hypot(*m), 1, axis=0) 
#        mark point at frequency of at least 1/.5 pixels along the "width" of 
#        the thickened line 
        intervals = np.linspace(-thickness, 
                                 thickness, 
                                 2*np.ceil(thickness/0.5).astype(int) + 1) 
        intervals = m.T[:,:,None]*intervals[None,None,:]
#        axes of p : 
#        axis=0 -- points along the (interpolated) polyline ("length") 
#        axis=1 -- x and y coordinates 
#        axis=2 -- points along thickened line ("width")
        p = points[:,:,None] + intervals
#        pad array allong the length axis if periodic 
        if self.periodic: 
            p = np.concatenate([p, p[0,:,:][None,:,:]])
#        centroids of each polygon 
#        last two dimensions are 'faked' length and width to create 
#        2d moving window 
        s, sh = np.array(p.strides), np.array(p.shape)
        self.cx, self.cy = as_strided(p, 
                                      np.concatenate([sh[[1,2,0]]-[0,1,1], [2,2]]), 
                                      s[[1,2,0,2,0]])            .mean((-2,-1)) 
#        Area of each polygon http://mathworld.wolfram.com/PolygonArea.html 
#        That is, the area is equal to half the sum of the determinant of 
#        sequential coordinates. In this case, the polygons are four-sided, and 
#        therefore each contain two sets of such coordinates going in opposite 
#        directions, i.e. along the polygon 'length' and 'width'. Half the  
#        sum of differences of determinants along the 'length' and 'width' 
#        therefore is the area. 
#        (Recall that if r1 and r2 are vectors representing the coordinates of 
#         two points, det(r1, r2) = -det(r2, r1) ). 
#        To increase performance we also use the fact that every polygon shares 
#        a side with its neighbor. In this way, we avoid calculating each 
#        determinant twice. 

#        det = lambda x: np.exp(np.linalg.slogdet(x)[1])
        det = lambda x: np.abs(np.linalg.det(x))
        diff = lambda x, axis: np.abs(np.diff(x, axis=axis))
#        determinant difference along the length 
        dl = diff(det(as_strided(p, 
                                 np.concatenate([sh[[0,2]]-[1,0], [2,2]]), 
                                 s[[0,2,1,0]])), 
                  axis=1)
#        determinant difference along the width 
        dw = diff(det(as_strided(p, 
                                 np.concatenate([sh[[0,2]]-[0,1], [2,2]]), 
                                 s[[0,2,1,2]])), 
                  axis=0)
        self.areas = 0.5*(dl + dw)
        
    def intensity_profile(self, rbs, thickness=None): 
        """
        Evaluate signal intensity along the length of the polyline. 
        
        Parameters
        ----------
        rbs : scipy.interpolate.RectBivariateSpline 
        
        thickness : float 
            Width to expand the polyline on either side, i.e. total thickness 
            is 2*thickness. 0 is a valid input, in which case interpolated 
            intensity along the line is returned. 
        """
        try: 
            if thickness is None: 
                thickness = self.thickness 
            else: 
                thickness = self._check_thickness(thickness)
                self._intensity_prep(thickness)
        except AttributeError: 
            thickness = self._check_thickness(1.5) # default thickness=1.5
            self._intensity_prep(thickness)
            
        x, y = self.cx, self.cy
        areas = self.areas

        sh = self.areas.shape
        return (rbs.ev(x.ravel(), y.ravel()).reshape(sh)*areas).sum(1)

    @property
    def center(self): 
        return self.points.mean(0)

class EllipseROI(PolylineROI): 
    """
    Essentially a polyline in the shape of an oval. Parameters are any set of 
    points that can be fit to an ellipse. 
    """
    def __init__(self, points, periodic=True, filled=False): 
#        points is four control points of ellipse 
        self.filled = filled 
        self.points = self._fit_ellipse(points) 
        self.periodic = True
        self._set_bounding_box()
    
    def _fit_ellipse(self, p): # UNTESTED
        """
        Fit ellipse to points parameter; then determine the xy coordinates 
        along the ellipse that are at most half a pixel apart. We use 
        EllipseModel.predict_xy() to estimate the xy coordinates along the 
        ellipse. As the parameter to predict_xy() is the set of angles along 
        the ellipse, we must first determine the radian interval that results 
        in a distance (arc length) of maximum 0.5 pixels apart between xy 
        points. (This arc length starts at pi/4 or 0, depending on which of 
        the width or height of the ellipse is longer). 
        """
        def get_arc_length_func(_a, _b): 
            return lambda _t:np.sqrt(_a**2*np.sin(_t)**2 + _b**2*np.cos(_t)**2)
        
        el = EllipseModel()
        assert(el.estimate(p))
        a, b = el.params[2], el.params[3] # width and height of ellipse 
        self._center = np.array([el.params[0], el.params[1]])
        if a < b: 
            stop = np.pi/4 # whether maximum arc length is around np.pi/4 or 0
        else: 
            stop  = 0. 
        
        t = np.pi/8 # radians along the ellipse 
        arc_length = 1. 
        arc_length_func = get_arc_length_func(a, b)
        while arc_length > 0.5: 
            t = t*0.75 
#            ellipse arc length 
#            https://math.stackexchange.com/questions/433094/how-to-determine-the-arc-length-of-ellipse
            arc_length = quad(arc_length_func, stop - t, stop)[0]
        circumfrence = quad(arc_length_func, 0, 2*np.pi)[0]
        n = circumfrence // t + 1
        intervals = np.linspace(0, 2*np.pi, n, endpoint=False)
        return el.predict_xy(intervals)

    @property
    def center(self): 
        return self._center 


class LineROI(PolylineROI): 
    filled = False
    def __init__(self, points): 
        """
        points : numpy.ndarray 
            Nx2 array of x, y coordinates in pixels. 
        """
        kwargs = {'k':1, 'per':False}
        self.points = self._spline(points, **kwargs)
        self._set_bounding_box()

    def _check_thickness(self, *args, **kwargs): 
        raise NotImplementedError("Line ROI can be any thickness. " 
                                  + "No need to check.")
    
    def intensity_profile(self, rbs, thickness=None): 
        """
        Evaluate signal intensity along the length of the line. 
        
        Parameters
        ----------
        rbs : scipy.interpolate.RectBivariateSpline 
            Spline object generated from the image. 
        
        thickness : float 
            Width to expand the polyline on either side, i.e. total thickness 
            is 2*thickness. 0 is a valid input, in which case interpolated 
            intensity along the line is return. 
        """
        try: 
            if thickness is None: 
                thickness = self.thickness 
        except AttributeError: 
            self._intensity_prep(1.5) # default line width
            
        x, y = self.cx, self.cy
        areas = self.areas
        sh = self.areas.shape
        return (rbs.ev(x.ravel(), y.ravel()).reshape(sh)*areas).sum(1) 
    
    def distance_from_line(self, point): 
        """
        Calculate shortest distance of a point from this line. 
        """
#        placeholder/reminder; will implement later 
        raise NotImplementedError
