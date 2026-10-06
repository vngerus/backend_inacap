import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from PIL import Image

MAX_FOTO_BYTES = 5 * 1024 * 1024
EXTENSIONES_FOTO = {".jpg", ".jpeg", ".png", ".webp"}
FORMATOS_FOTO = {"JPEG", "PNG", "WEBP"}


def foto_path(instance, filename):
    """Nombre aleatorio: no se confía en el nombre que manda el cliente."""
    extension = os.path.splitext(filename)[1].lower()
    return f"{instance._meta.model_name}/{uuid4().hex}{extension}"


def validar_foto(archivo):
    if archivo.size > MAX_FOTO_BYTES:
        raise ValidationError("La foto no puede superar los 5 MB.")
    if os.path.splitext(archivo.name)[1].lower() not in EXTENSIONES_FOTO:
        raise ValidationError("Extensión no permitida: usa jpg, png o webp.")
    try:
        formato = Image.open(archivo).format  # Pillow lee el contenido real, no la extensión
    except Exception:
        raise ValidationError("El archivo no es una imagen válida.")
    finally:
        archivo.seek(0)
    if formato not in FORMATOS_FOTO:
        raise ValidationError("Formato no permitido: usa jpg, png o webp.")
