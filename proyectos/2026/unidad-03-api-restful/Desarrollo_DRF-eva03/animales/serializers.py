from rest_framework import serializers

from .models import Animal


class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = (
            "id", "nombre", "especie", "sexo", "edad_meses", "descripcion",
            "foto", "estado", "refugio", "creado",
        )
        read_only_fields = ("id", "creado")
