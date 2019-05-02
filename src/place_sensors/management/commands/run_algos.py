import os

from luigi import build
from django.core.management import BaseCommand
from django.contrib.gis.geos import GEOSGeometry

from place_sensors.models import Locations, Sensors, SensorPlacements

from final_project.tasks.cov_algo import PlaceSensorTask


class Command(BaseCommand):
    """ Command to run the algorithms for a given sensor"""

    help = "run placement algorithms"
    OUTPUT_ROOT = os.path.join('data', 'sensor_wkt/')  # path to look for results

    def add_arguments(self, parser):
        parser.add_argument("-r", "--radar", action="store_true")
        parser.add_argument("-c", "--camera", action="store_true")

    def handle(self, *args, **options):
        # TODO: Need to handle the case in which multiple sensor types are passed
        if options['radar']:
            s = Sensors.objects.filter(stype='Radar')
        elif options['camera']:
            s = Sensors.objects.filter(stype='Camera')
        else:
            return

        # delete the existing sensor placements from the db
        if SensorPlacements.objects.filter(sensor=s[0]):
            SensorPlacements.objects.filter(sensor=s[0]).delete()

        # create a luigi task list, parameterized by sensors & its specs
        # note: as sensor specs are significant parameters, if they are changed,
        # the task would run again. this is as per design
        task_list = []
        for site in Locations.objects.all():
            # TODO: Serialize sensor & site objects and pass them as luigi parameters
            task_list.append(PlaceSensorTask(site.name, s[0].stype, s[0].rng, s[0].fov))

        # run the sensor placement tasks
        build(task_list, local_scheduler=True)

        # write the results from each sensor placements in the db
        # TODO: Add db write into luigi tasks? Need to build django support in luigi
        for site in Locations.objects.all():
            mpoly_file = os.path.join(self.OUTPUT_ROOT, "{}_{}".format(site, s[0].stype))
            with open(mpoly_file, 'r') as f:
                mpoly_wkt = f.read()
            p = SensorPlacements(site=site, sensor=s[0], placement=GEOSGeometry(mpoly_wkt))
            p.save()


