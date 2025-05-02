from django.db import models
from django.conf import settings

class Application(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    url         = models.CharField(
        max_length=255,
        help_text="Ruta interna (p.ej. /consignaciones-atico/)"
    )
    users       = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="applications",
        help_text="Usuarios que pueden ver esta app"
    )

    def __str__(self):
        return self.name
