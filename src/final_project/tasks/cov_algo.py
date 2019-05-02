import os
from math import sqrt, ceil, pi, cos, sin
from collections import namedtuple

import numpy as np

from luigi import Task, LocalTarget, Parameter, IntParameter
from django.contrib.gis.gdal import SpatialReference, CoordTransform, OGRGeomType
from django.contrib.gis.geos import LinearRing, LineString, Polygon, MultiPolygon, GEOSGeometry


class PlaceSensorTask(Task):
    """luigi task for calculating sensor placements"""

    INPUT_ROOT = os.path.join('data', 'site_wkt/')
    OUTPUT_ROOT = os.path.join('data', 'sensor_wkt/')
    site = Parameter()  # luigi parameter for site name
    sensor_stype = Parameter()  # luigi parameter for sensor type
    sensor_rng = IntParameter()  # luigi parameter for sensor range
    sensor_fov = IntParameter()  # luigi parameter for sensor fov

    def requires(self):
        return []

    def output(self):
        # return the placement of sensors in Well Known Text (wkt) format
        return LocalTarget(os.path.join(self.OUTPUT_ROOT, "{}_{}".format(self.site, self.sensor_stype)))

    def run(self):
        site_file = os.path.join(self.INPUT_ROOT, self.site)
        with open(site_file, 'r') as f:
            poly_wkt = f.read()

        poly = GEOSGeometry(poly_wkt)
        # convert from lat-long to utm (xy)
        wgsProj = SpatialReference('+proj=longlat +datum=WGS84')
        utmProj = SpatialReference('+proj=utm +zone=18 +ellps=WGS84')

        ct = CoordTransform(wgsProj, utmProj)
        poly.transform(ct)
        # pass the polygon in form of lines in a numpy array
        xy = np.asarray(poly.tuple[0])

        sps = placeSensor(xy, rng=self.sensor_rng, fov=self.sensor_fov, skip_small=True)

        ct = CoordTransform(utmProj, wgsProj)
        sps.transform(ct)
        with self.output().open('w') as f:
            f.write(sps.wkt)
        

def placeSensor(xy, rng=20, fov=10, split_on_turns=False, skip_small=False):
    """
    algorithm to place sensors optimally

    Args:
    xy: numpy array containing the line segments for the outline.
    rng:integer giving range of sensor. Default 20.
    fov: integer giving fov of sensor. Default 10.
    split_on_turns: allow segments to split on turns. Default False.
    skip_small: skip small remaining segment parts in each line segments.

    Returns:
    sps: MultiPolygon datatype containing the sensor placement polygons.

    """

    # no of points
    n = xy.shape[0]

    # create line segments from the polyline
    linedf = np.zeros((n-1, 4), dtype=float)
    np.copyto(linedf[:, 0], xy[0:n-1, 0])
    np.copyto(linedf[:, 1], xy[0:n-1, 1])
    np.copyto(linedf[:, 2], xy[1:n, 0])
    np.copyto(linedf[:, 3], xy[1:n, 1])

    xl = 0
    yl = 0
    dfx = [] # list of sensor x coordinates
    dfy = [] # list of sensor y coordinates
    sl_total = 0
    lp = []  # list of polygons
  
    residual_seg_length = 0
    # named tuple for the line segment
    seg = namedtuple('seg', ['x1', 'y1', 'x2', 'y2'])

    # basic splitting code from:
    # # https://stackoverflow.com/questions/38700246/how-do-i-split-divide-polyline-shapefiles-into-equally-length-smaller-segments
    for i in range(linedf.shape[0]):
        # for each line of the calculate segment length   
        v_seg = seg(linedf[i, 0], linedf[i, 1], linedf[i, 2], linedf[i, 3])
        
        seg_length = sqrt((v_seg.x1 - v_seg.x2)**2 + (v_seg.y1 - v_seg.y2)**2)  # current segment length
        sl_total = sl_total + seg_length  # total segment length

        dis_last = sqrt((v_seg.x2 - xl)**2 + (v_seg.y2 - yl)**2)  # distance from last sensor
        # if current segment is less than 25% of sensor range, then assume
        # previous sensor will be oriented to handle this
        if (i > 0) and ((sl_total < rng * 0.5) or (dis_last < rng * 0.25)) * skip_small :
            continue

        line_seg = LineString([(v_seg.x1, v_seg.y1), (v_seg.x2, v_seg.y2)])

        # if(i > 0) and sps.contains(l):
        #     continue

        # check if the current line segment is being monitor by a previously placed sensor
        if i > 0:
            for p in sps:
                igeom = p.intersection(line_seg)
                if igeom.geom_type == OGRGeomType('Point'):
                    x = igeom.tuple[0]
                    y = igeom.tuple[1]
                    residual_seg_length = sqrt((v_seg.x1 - x)**2 + (v_seg.y1 - y)**2)
                    # print("point intersection!")        
                    continue
                elif igeom.geom_type == OGRGeomType('LineString'):
                    x = igeom.tuple[1][0]
                    y = igeom.tuple[1][1]
                    residual_seg_length = sqrt((v_seg.x1 - x)**2 + (v_seg.y1 - y)**2)
                    # print("line intersection!")   
                    continue
                else:
                    x = 0
                    y = 0

        # u is vector along the segment & ux,uy are length of unit vectors along x & y
        u = sqrt((v_seg.x2 - v_seg.x1)**2 + (v_seg.y2 - v_seg.y1)**2)
        ux = (v_seg.x2 - v_seg.x1)/u
        uy = (v_seg.y2 - v_seg.y1)/u
    
        # calculate number of segment the segment is split into
        num_seg = ceil((seg_length - residual_seg_length) / rng)
    
        # skip if next vertex is before interval_length
        if num_seg >= 0:      
      
            # add interpolated segments
            for j in range(num_seg):
                slx = v_seg.x1 + ux * residual_seg_length + ux * rng * j - v_seg.x2
                sly = v_seg.y1 + uy * residual_seg_length + uy * rng * j - v_seg.y2
                sl = sqrt(slx**2 + sly**2)

                # if the remaining segment is small, skip and it would be taken care in manual adjustments
                if(i > 1) & ((sl < rng * 0.25) & (sl_total < rng * 0.5)) & skip_small:
                    break
                
                dfx.append(v_seg.x1 + ux * residual_seg_length + ux * rng * j)
                dfy.append(v_seg.y1 + uy * residual_seg_length + uy * rng * j)
                
                sl_total = 0
                t = (fov / 180.0) * pi
                x0 = dfx[-1]
                x = ux * rng
                y0 = dfy[-1]
                y = uy * rng

                coords = []

                coords.append((x0,y0))
                # create an arc with line segments
                numSegs = ceil(fov/4)
                for s in range(1,numSegs+1, 1):
                    coords.append((x*cos(t/s) - y*sin(t/s) + x0, y*cos(t/s) + x*sin(t/s) + y0))
                for s in range(-numSegs,0, 1):
                    coords.append((x*cos(t/s) - y*sin(t/s) + x0, y*cos(t/s) + x*sin(t/s) + y0))
                # close the Polygon
                coords.append((x0, y0))
                p = Polygon(LinearRing(coords))

                # list of Polygon's
                lp.append(p)

                xl = x0
                yl = y0

            # convert list into MultiPolygon
            sps = MultiPolygon(lp)

        else:
            if split_on_turns:
                residual_seg_length = residual_seg_length - seg_length
            else:
                residual_seg_length = 0
            continue
    
        # calculate residual segment length
        if split_on_turns:
            residual_seg_length = rng - ((seg_length - residual_seg_length) - (num_seg * rng))
        else:
            residual_seg_length = 0

    return sps
