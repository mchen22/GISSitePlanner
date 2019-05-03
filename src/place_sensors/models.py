from django.contrib.gis.db import models


class Locations(models.Model):
    """Stores the site details & outline fields"""

    name = models.CharField(max_length=50)
    outline = models.PolygonField()

    def __str__(self):
        return self.name

    
class Sensors(models.Model):
    """Stores the sensor information fields"""

    stype = models.CharField(max_length=50)  # sensor type: Radar, Camera
    name = models.CharField(max_length=50)  # user friendly name for sensor
    fov = models.IntegerField(default=10)  # field of view of the sensor
    rng = models.IntegerField(default=50)  # range of the sensor

    def __str__(self):
        return '{}({})'.format(self.name, self.stype)


class SensorPlacements(models.Model):
    """Stores the sensor placement details"""

    site = models.ForeignKey(Locations, on_delete=models.CASCADE)  # site
    sensor = models.ForeignKey(Sensors, on_delete=models.CASCADE)  # type of sensor
    placement = models.MultiPolygonField()  # sensor placement multipolygons

    class Meta:
        unique_together = ('site', 'sensor', )
    
    def perimeter(self):
        return self.site.outline

    def __str__(self):
        return '{}({})'.format(self.site.name, self.sensor.stype)
