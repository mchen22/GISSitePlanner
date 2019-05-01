from django.core.management import BaseCommand
from django.db import transaction

from collections import namedtuple

from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import Polygon, LinearRing
from django.contrib.gis.geos import GEOSGeometry

from place_sensors.models import Locations, Sensors, SensorPlacements

import numpy as np

class Command(BaseCommand):
    help = "Load Site Data from kml"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="kml file name")
        parser.add_argument("-r", "--radar", action="store_true")
        parser.add_argument("-c", "--camera", action="store_true")

    def handle(self, *args, **options):
        kmlfile = options['file']

        # clear the DBs
        Locations.objects.all().delete()
        Sensors.objects.all().delete()
        SensorPlacements.objects.all().delete()

        # load the data
        ds = DataSource(kmlfile)
        layer = ds[0]

        for feat in layer:
            site = feat.get('Name')
            print(site)
            poly = feat.geom
            # important: converting from 3D to 2D
            poly = Polygon(LinearRing([(pt[0], pt[1]) for pt in poly.tuple[0]]), srid=4326)
            print(poly.geom_type)
            print(poly.wkt)
            l = Locations(name = site, outline=poly)
            l.save()
        
        if options['radar']:
            r = Sensors(stype='Radar', name='vendor1', fov=45, rng=200)
            r.save()
        
        if options['camera']:
            c = Sensors(stype='Camera', name='vendor1', fov=10, rng=50)
            c.save()


