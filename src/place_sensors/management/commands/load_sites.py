import os

from django.core.management import BaseCommand
from django.db import transaction

from collections import namedtuple

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Polygon, LinearRing
from django.contrib.gis.geos import GEOSGeometry

from place_sensors.models import Locations, Sensors, SensorPlacements
from pset_utils.io import atomic_write

class Command(BaseCommand):
    help = "Load Site Data from kml"
    INPUT_ROOT = os.path.join('data', 'site_wkt/')

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

        for fp in os.listdir(self.INPUT_ROOT):
            file_path = os.path.join(self.INPUT_ROOT, fp)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # load the data
        ds = DataSource(kmlfile)
        layer = ds[0]

        for feat in layer:
            site = feat.get('Name')
            print(site)
            poly = feat.geom
            # important: converting from 3D to 2D
            poly = Polygon(LinearRing([(pt[0], pt[1]) for pt in poly.tuple[0]]), srid=4326)
            l = Locations(name = site, outline=poly)
            l.save()

            fp = os.path.join(self.INPUT_ROOT,site)
            with atomic_write(fp, 'w') as f:
                f.write(poly.wkt)

        s = Sensors(stype='Radar', name='vendor1', fov=45, rng=200)
        s.save()

        s = Sensors(stype='Camera', name='vendor1', fov=10, rng=50)
        s.save()



