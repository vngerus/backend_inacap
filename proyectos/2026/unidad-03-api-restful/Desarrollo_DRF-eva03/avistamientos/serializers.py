from django.utils import timezone
from rest_framework import serializers

from .models import Avistamiento


class AvistamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avistamiento
        fields = (
            "id", "reportante", "especie", "descripcion", "lugar", "lat", "lng",
            "foto", "fecha_avistamiento", "estado", "animal", "creado",
        )
        read_only_fields = ("id", "reportante", "estado", "animal", "creado")

    def validate_fecha_avistamiento(self, fecha):
        if fecha > timezone.localdate():
            raise serializers.ValidationError("La fecha del avistamiento no puede ser futura.")
        return fecha


class ConvertirSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100, required=False, allow_blank=True)
