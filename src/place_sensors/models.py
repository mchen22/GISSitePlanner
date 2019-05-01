# from django.db import models
from django.contrib.gis.db import models


class Locations(models.Model):
    """Stores the site name & outline fields"""

    name = models.CharField(max_length=50)
    outline = models.PolygonField()

    
class Sensors(models.Model):
    """Stores the sensor information fields"""

    stype = models.CharField(max_length=50) # sensor type: Radar, Camera
    name = models.CharField(max_length=50) # user friendly name for sensor
    fov = models.IntegerField(default=10) # field of view of the sensor
    rng = models.IntegerField(default=50) # range of the sensor


class SensorPlacements(models.Model):
    """Stores the statistics"""

    site = models.ForeignKey(Locations, on_delete=models.CASCADE) # site
    sensor = models.ForeignKey(Sensors, on_delete=models.CASCADE) # type of sensor
    placement = models.MultiPolygonField() # sensor placement polygons

    class Meta:
        unique_together = ('site', 'sensor', )
    
