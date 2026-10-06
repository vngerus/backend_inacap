from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from animales.models import Animal
from config.exceptions import Conflicto


class SolicitudAdopcion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"
        CANCELADA = "cancelada", "Cancelada"

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="solicitudes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solicitudes")
    mensaje = models.TextField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)
    resuelta = models.DateTimeField(null=True, blank=True)
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="solicitudes_resueltas"
    )

    class Meta:
        ordering = ["-creada", "-id"]
        constraints = [
            # respaldo en la base de datos de la regla "una pendiente por usuario y animal"
            models.UniqueConstraint(
                fields=["animal", "usuario"],
                condition=models.Q(estado="pendiente"),
                name="una_pendiente_por_usuario_y_animal",
            )
        ]

    def _resolver(self, estado, por=None):
        if self.estado != self.Estado.PENDIENTE:
            raise Conflicto("La solicitud ya fue resuelta.")
        self.estado = estado
        self.resuelta = timezone.now()
        self.resuelta_por = por
        self.save()

    def aprobar(self, por):
        with transaction.atomic():
            animal = Animal.objects.select_for_update().get(pk=self.animal_id)
            if animal.estado != Animal.Estado.ADOPTABLE:
                raise Conflicto("El animal ya fue adoptado.")
            self._resolver(self.Estado.APROBADA, por)
            animal.estado = Animal.Estado.ADOPTADO
            animal.save(update_fields=["estado"])
            SolicitudAdopcion.objects.filter(animal=animal, estado=self.Estado.PENDIENTE).update(
                estado=self.Estado.RECHAZADA, resuelta=timezone.now(), resuelta_por=por
            )

    def rechazar(self, por):
        self._resolver(self.Estado.RECHAZADA, por)

    def cancelar(self):
        self._resolver(self.Estado.CANCELADA)
