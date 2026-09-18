from django.db import models


class Dueno(models.Model):
    nombre = models.CharField(max_length=80)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre


class Michi(models.Model):
    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)
    dueno = models.ForeignKey(
        Dueno, on_delete=models.CASCADE, related_name='michis',
        null=True, blank=True,
    )
    foto = models.ImageField(upload_to='michis/', blank=True, null=True)

    def __str__(self):
        return self.nombre