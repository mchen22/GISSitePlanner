from django.test import TestCase as DJTest
from django.contrib.gis.geos import GEOSGeometry

from place_sensors.models import Locations, Sensors, SensorPlacements


class LocationsTests(DJTest):
    poly = GEOSGeometry("POLYGON (( \
                    -77.05788457660967 38.87253259892824 100, \
                    -77.05465973756702 38.87291016281703 100, \
                    -77.05315536854791 38.87053267794386 100, \
                    -77.05552622493516 38.868757801256 100, \
                    -77.05844056290393 38.86996206506943 100, \
                    -77.05788457660967 38.87253259892824 100 \
                    ))")

    def setUp(self):
        Locations.objects.create(name="site1",
                                 outline=self.poly
                                 )

    def LocationsTestsData(self):
        """Animals that can speak are correctly identified"""
        s1 = Locations.objects.get(name="site1")
        self.assertEqual(s1.outline, self.poly)
        self.assertEqual(s1, "site1")

