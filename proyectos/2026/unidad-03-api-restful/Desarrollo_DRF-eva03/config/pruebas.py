import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APITestCase

User = get_user_model()
CLAVE = "Clave-Segura-123"
MEDIA_TEMPORAL = tempfile.mkdtemp()  # las fotos de los tests no tocan media/


def imagen(nombre="foto.png", formato="PNG"):
    buf = BytesIO()
    Image.new("RGB", (10, 10), "orange").save(buf, formato)
    return SimpleUploadedFile(nombre, buf.getvalue(), content_type=f"image/{formato.lower()}")


class BaseAPITest(APITestCase):
    def setUp(self):
        cache.clear()  # el throttling vive en el cache: aislar cada test
        self.adoptante = User.objects.create_user("ana", "ana@x.cl", CLAVE)
        self.otro = User.objects.create_user("beto", "beto@x.cl", CLAVE)
        self.staff = User.objects.create_user("sofia", "sofia@x.cl", CLAVE, is_staff=True)
        self.admin = User.objects.create_superuser("admin", "admin@x.cl", CLAVE)
