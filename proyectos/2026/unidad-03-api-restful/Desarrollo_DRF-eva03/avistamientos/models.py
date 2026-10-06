from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from animales.models import Animal
from config.exceptions import Conflicto
from config.uploads import foto_path, validar_foto


class Avistamiento(models.Model):
    class Estado(models.TextChoices):
        REPORTADO = "reportado", "Reportado"
        VERIFICADO = "verificado", "Verificado"
        DESCARTADO = "descartado", "Descartado"

    reportante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avistamientos")
    especie = models.CharField(max_length=10, choices=Animal.Especie.choices)
    descripcion = models.TextField()
    lugar = models.CharField(max_length=200)
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    foto = models.ImageField(upload_to=foto_path, blank=True, validators=[validar_foto])
    fecha_avistamiento = models.DateField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.REPORTADO)
    animal = models.OneToOneField(Animal, on_delete=models.SET_NULL, null=True, blank=True, related_name="avistamiento")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado", "-id"]

    def _resolver(self, estado):
        if self.estado != self.Estado.REPORTADO:
            raise Conflicto("El avistamiento ya fue resuelto.")
        self.estado = estado
        self.save(update_fields=["estado"])

    def verificar(self):
        self._resolver(self.Estado.VERIFICADO)

    def descartar(self):
        self._resolver(self.Estado.DESCARTADO)

    def convertir(self, nombre=""):
        with transaction.atomic():
            if self.animal_id:
                raise Conflicto("El avistamiento ya fue convertido en animal.")
            if self.estado != self.Estado.VERIFICADO:
                raise Conflicto("Solo se convierten avistamientos verificados.")
            self.animal = Animal.objects.create(
                nombre=nombre or f"Avistado #{self.pk}",
                especie=self.especie,
                descripcion=self.descripcion,
                foto=self.foto.name,  # ponytail: comparte el archivo, no lo duplica
            )
            self.save(update_fields=["animal"])
        return self.animal
