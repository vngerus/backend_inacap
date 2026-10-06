from django.db import models

from config.uploads import foto_path, validar_foto


class Animal(models.Model):
    class Especie(models.TextChoices):
        PERRO = "perro", "Perro"
        GATO = "gato", "Gato"
        OTRO = "otro", "Otro"

    class Sexo(models.TextChoices):
        MACHO = "macho", "Macho"
        HEMBRA = "hembra", "Hembra"
        DESCONOCIDO = "desconocido", "Desconocido"

    class Estado(models.TextChoices):
        ADOPTABLE = "adoptable", "Adoptable"
        ADOPTADO = "adoptado", "Adoptado"

    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=10, choices=Especie.choices)
    sexo = models.CharField(max_length=12, choices=Sexo.choices, default=Sexo.DESCONOCIDO)
    edad_meses = models.PositiveIntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    foto = models.ImageField(upload_to=foto_path, blank=True, validators=[validar_foto])
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ADOPTABLE)
    refugio = models.CharField(max_length=100, blank=True)  # ponytail: texto; pasar a modelo si hace falta gestionar refugios
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado", "-id"]  # orden estable para la paginación

    def __str__(self):
        return self.nombre
