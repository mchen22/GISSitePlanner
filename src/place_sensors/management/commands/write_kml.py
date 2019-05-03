import os

from django.core.management import BaseCommand
from django.template import loader

from place_sensors.models import SensorPlacements


class Command(BaseCommand):
    """ Command to write the sensor coverage to kml """

    help = "write calculated sensor coverage to kml"
    OUTPUT_ROOT = os.path.join('data', 'sensor_kml/')  # path to look for results

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # clear all the existing kmls
        for fp in os.listdir(self.OUTPUT_ROOT):
            file_path = os.path.join(self.OUTPUT_ROOT, fp)
            if os.path.isfile(file_path):
                if not (fp == ".gitkeep"):
                    os.unlink(file_path)

        # template reference:
        # https://developers.google.com/kml/documentation/kmlreference
        for sp in SensorPlacements.objects.all():
            mpoly = sp.placement
            site = sp.site.name
            outline = sp.site.outline
            stype = sp.sensor.stype

            mpoly_file = os.path.join(self.OUTPUT_ROOT, "{}_{}.kml".format(site, stype))
            k = loader.render_to_string('site.kml',
                                        {'site_name': site, 'sensor_name': stype, 'poly': mpoly, 'outline': outline})

            with open(mpoly_file, 'w') as f:
                f.write(k)

