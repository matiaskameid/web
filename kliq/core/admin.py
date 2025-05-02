from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display         = ("name", "slug", "url")
    prepopulated_fields  = {"slug": ("name",)}
    filter_horizontal    = ("users",)
