from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from animales.models import Animal
from config.pruebas import MEDIA_TEMPORAL, BaseAPITest, imagen
from config.uploads import MAX_FOTO_BYTES, validar_foto

URL = "/api/v1/animales/"


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class AnimalesTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.firulais = Animal.objects.create(nombre="Firulais", especie="perro", refugio="Huellitas")
        self.misu = Animal.objects.create(nombre="Misu", especie="gato", estado="adoptado")

    def crear(self, **extra):
        datos = {"nombre": "Rex", "especie": "perro", **extra}
        return self.client.post(URL, datos, format="multipart")

    # --- lectura pública ---
    def test_lista_es_publica_paginada_y_json(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})

    def test_filtros_y_busqueda(self):
        self.assertEqual(self.client.get(URL, {"especie": "gato"}).data["count"], 1)
        self.assertEqual(self.client.get(URL, {"estado": "adoptable"}).data["count"], 1)
        self.assertEqual(self.client.get(URL, {"search": "huellitas"}).data["count"], 1)

    def test_detalle_publico_y_404(self):
        self.assertEqual(self.client.get(f"{URL}{self.firulais.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"{URL}9999/").status_code, 404)

    # --- escritura por rol ---
    def test_anonimo_y_adoptante_no_crean(self):
        self.assertEqual(self.crear().status_code, 401)
        self.client.force_authenticate(self.adoptante)
        self.assertEqual(self.crear().status_code, 403)

    def test_staff_crea_animal_adoptable_por_defecto(self):
        self.client.force_authenticate(self.staff)
        response = self.crear()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["estado"], "adoptable")
        self.assertEqual(response.data["sexo"], "desconocido")

    def test_staff_marca_animal_como_adoptado(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(f"{URL}{self.firulais.pk}/", {"estado": "adoptado"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_solo_admin_borra(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(f"{URL}{self.firulais.pk}/").status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f"{URL}{self.firulais.pk}/").status_code, 204)

    def test_validaciones_de_campos(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.crear(especie="dragon").status_code, 400)
        self.assertEqual(self.crear(edad_meses=-3).status_code, 400)

    # --- fotos ---
    def test_foto_valida_se_guarda_con_nombre_uuid(self):
        self.client.force_authenticate(self.staff)
        response = self.crear(foto=imagen("mi foto de Rex.png"))
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["foto"].endswith(".png"))
        self.assertNotIn("Rex", response.data["foto"])

    def test_foto_con_contenido_que_no_es_imagen(self):
        self.client.force_authenticate(self.staff)
        falsa = SimpleUploadedFile("virus.png", b"esto no es una imagen", content_type="image/png")
        self.assertEqual(self.crear(foto=falsa).status_code, 400)

    def test_foto_con_extension_peligrosa(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.crear(foto=imagen("pagina.html")).status_code, 400)

    def test_foto_con_formato_no_permitido(self):
        self.client.force_authenticate(self.staff)
        gif_disfrazado = imagen("foto.png", "GIF")  # contenido GIF, extensión .png
        self.assertEqual(self.crear(foto=gif_disfrazado).status_code, 400)

    def test_foto_mayor_a_5mb(self):
        grande = SimpleUploadedFile(
            "grande.png", imagen().read() + b"0" * (MAX_FOTO_BYTES + 1), content_type="image/png"
        )
        with self.assertRaises(ValidationError):
            validar_foto(grande)
