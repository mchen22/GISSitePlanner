import os

from django.core.management import BaseCommand
from django.contrib.gis.geos import GEOSGeometry

from place_sensors.models import Locations, Sensors, SensorPlacements

from luigi import build

from final_project.tasks.cov_algo import PlaceSensorTask
from pset_utils.io import atomic_write

class Command(BaseCommand):
    help = "run placement algorithms"
    OUTPUT_ROOT = os.path.join('data', 'sensor_wkt/')

    def add_arguments(self, parser):
        parser.add_argument("-r", "--radar", action="store_true")
        parser.add_argument("-c", "--camera", action="store_true")

    def handle(self, *args, **options):

        if options['radar']:
            s = Sensors.objects.filter(stype='Radar')
        elif options['camera']:
            s = Sensors.objects.filter(stype='Camera')
        else:
            return

        if SensorPlacements.objects.filter(sensor=s[0]):
            SensorPlacements.objects.filter(sensor=s[0]).delete()

        task_list = []
        for site in Locations.objects.all():
            task_list.append(PlaceSensorTask(site.name,s[0].stype,s[0].rng,s[0].fov))

        print(task_list)
        build(task_list, local_scheduler=True)

        for site in Locations.objects.all():
            mpoly_file = os.path.join(self.OUTPUT_ROOT, "{}_{}".format(site, s[0].stype))
            with open(mpoly_file, 'r') as f:
                mpoly_wkt = f.read()
            p = SensorPlacements(site=site, sensor=s[0], placement=GEOSGeometry(mpoly_wkt))
            p.save()


