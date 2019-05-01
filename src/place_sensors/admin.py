# from django.contrib import admin
from django.contrib.gis import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from place_sensors.models import Locations, Sensors, SensorPlacements

# Register your models here.
admin.site.register(Locations, admin.OSMGeoAdmin)
admin.site.register(Sensors, admin.OSMGeoAdmin)
# admin.site.register(SensorPlacements, admin.OSMGeoAdmin)

@admin.register(SensorPlacements)
class SensorPlacementsAdmin(admin.OSMGeoAdmin):
    fields = ('site', 'placement',)
    readonly_fields = ('site',)

