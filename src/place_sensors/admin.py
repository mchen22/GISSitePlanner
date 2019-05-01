from django.contrib import admin
from place_sensors.models import Locations, Sensors, SensorPlacements

# Register your models here.
admin.site.register(Locations)
admin.site.register(Sensors)
admin.site.register(SensorPlacements)