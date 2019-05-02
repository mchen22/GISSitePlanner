import os
from math import sqrt, ceil, pi, cos, sin
from collections import namedtuple

import numpy as np
from luigi import Task, LocalTarget, Parameter, IntParameter

from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform, OGRGeomType
from django.contrib.gis.geos import LinearRing, LineString, Polygon, MultiPolygon, MultiLineString, MultiPolygon, GEOSGeometry

class PlaceSensorTask(Task):
    INPUT_ROOT = os.path.join('data', 'site_wkt/')
    OUTPUT_ROOT = os.path.join('data', 'sensor_wkt/')
    site = Parameter()  # luigi parameter for site
    sensor_stype =  Parameter() # luigi parameter for sensor type
    sensor_rng =  IntParameter() # luigi parameter for sensor range
    sensor_fov =  IntParameter() # luigi parameter for sensor fov

    def requires(self):
        return []

    def output(self):
        # return SuffixPreservingLocalTarget of the stylized image
        return LocalTarget(os.path.join(self.OUTPUT_ROOT, "{}_{}".format(self.site, self.sensor_stype)))

    def run(self):
        site_file = os.path.join(self.INPUT_ROOT,self.site)
        with open(site_file, 'r') as f:
            poly_wkt = f.read()

        poly = GEOSGeometry(poly_wkt)
        wgsProj = SpatialReference('+proj=longlat +datum=WGS84')
        utmProj = SpatialReference('+proj=utm +zone=18 +ellps=WGS84')

        ct = CoordTransform(wgsProj, utmProj)
        poly.transform(ct)
        xy = np.asarray(poly.tuple[0])
        # xy = xy[:-1,[0,1]]

        sps = PlaceSensor(xy, interval_length = self.sensor_rng, FOV = self.sensor_fov, add_final_point = False, 
            add_original_points = False, skip_small = True)

        ct = CoordTransform(utmProj, wgsProj)
        sps.transform(ct)
        with self.output().open('w') as f:
            f.write(sps.wkt)
        

def PlaceSensor(xy, interval_length = 20, display_length = 30, add_original_points = True, 
    add_final_point = False, split_on_turns = False, FOV = 10, skip_small = False):

    # no of points
    n = xy.shape[0]
    # print(n)
    # create line segments from the polyline
    linedf = np.zeros((n-1,4), dtype=float)
    np.copyto(linedf[:,0], xy[0:n-1,0])
    np.copyto(linedf[:,1], xy[0:n-1,1])
    np.copyto(linedf[:,2], xy[1:n,0])
    np.copyto(linedf[:,3], xy[1:n,1])

    xl = 0
    yl = 0
    sl_total = 0
    dfx = [] # list of sensor x coordinates
    dfy = [] # list of sensor y coordinates
    lp = [] # list of polygons
  
    residual_seg_length = 0
    # named tuple for the line segment
    seg = namedtuple('seg',['x1','y1','x2','y2'])

    for i in range(linedf.shape[0]):
        # for each line of the calculate segment length   
        v_seg = seg(linedf[i,0],linedf[i,1],linedf[i,2],linedf[i,3])
        
        seg_length = sqrt((v_seg.x1 - v_seg.x2)**2 + (v_seg.y1 - v_seg.y2)**2)
        # print(seg_length) 
        sl_total = sl_total + seg_length
        dis_last = sqrt((v_seg.x2 - xl)**2 + (v_seg.y2 - yl)**2) 
        # if current segment is less than 25% of sensor range, then assume
        # previous sensor will be oriented to handle this
        if (i > 0) and ((sl_total < interval_length*0.5) or (dis_last < interval_length*0.25)) * skip_small :
            continue

        l = LineString([(v_seg.x1, v_seg.y1), (v_seg.x2, v_seg.y2)])
        # ll.append(LineString([(v_seg.x1, v_seg.x2), (v_seg.y1, v_seg.y2)]))
        # sls = MultiLineString(ll)
        
        # if(i > 0) and sps.contains(l):
        #     continue

        if(i > 0):
            for p in (sps):
                igeom = p.intersection(l)
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
    
        u = sqrt((v_seg.x2 - v_seg.x1)**2 + (v_seg.y2 - v_seg.y1)**2)
        ux = (v_seg.x2 - v_seg.x1)/u
        uy = (v_seg.y2 - v_seg.y1)/u
    
        # calculate number of segment the segment is split into
        num_seg = ceil((seg_length - residual_seg_length)  /  interval_length)
    
        # skip if next vertex is before interval_length
        if num_seg >= 0:      
      
            # add interpolated segments
            for j in range(num_seg):
                slx = v_seg.x1  +  ux*residual_seg_length + ux*interval_length*j - v_seg.x2
                sly = v_seg.y1  +  uy*residual_seg_length + uy*interval_length*j - v_seg.y2
                sl = sqrt(slx**2 + sly**2)
                
                if(i > 1) & ((sl < interval_length*0.25)  & (sl_total < interval_length*0.5)) & skip_small:
                    break
                
                dfx.append(v_seg.x1 + ux*residual_seg_length + ux*interval_length*j)
                dfy.append(v_seg.y1 + uy*residual_seg_length + uy*interval_length*j)
                
                sl_total = 0
                t = (FOV/180.0)*pi
                x0 = dfx[-1]
                x = ux*interval_length
                y0 = dfy[-1]
                y = uy*interval_length

                coords = []
                coords.append((x0,y0))

                # create an arc with line segments
                numSegs = ceil(FOV/4)
                for s in range(1,numSegs+1,1):
                    coords.append((x*cos(t/s) - y*sin(t/s) + x0, y*cos(t/s) + x*sin(t/s) + y0))
                for s in range(-numSegs,0,1):
                    coords.append((x*cos(t/s) - y*sin(t/s) + x0, y*cos(t/s) + x*sin(t/s) + y0))     
                coords.append((x0,y0))
                p = Polygon(LinearRing(coords))

                lp.append(p)

                xl = x0
                yl = y0

            sps = MultiPolygon(lp)

            # add original point (optional)
            if add_original_points:
                dfx.append(v_seg.x2)
                dfy.append(v_seg.y2)
        else:
      
            # add original point (optional)
            if(add_original_points):
                dfx.append(v_seg.x2)
                dfy.append(v_seg.y2)
            
            if(split_on_turns):
                residual_seg_length = residual_seg_length - seg_length
            else:
                residual_seg_length = 0
          
            continue
    
        # calculate residual segment length
        if(split_on_turns):
            residual_seg_length = interval_length - ((seg_length - residual_seg_length) - (num_seg*interval_length))
        else:
            residual_seg_length = 0

    # add final point (optional)
    if(add_final_point):
        dfx.append(xy[n-1,0])
        dfy.append(xy[n-1,1])
    
    # sps = MultiPolygon(lp)
    # sprint(len(sps))
    return sps