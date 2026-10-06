from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from animales.models import Animal
from avistamientos.models import Avistamiento
from config.pruebas import MEDIA_TEMPORAL, BaseAPITest, imagen

URL = "/api/v1/avistamientos/"


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class AvistamientosTests(BaseAPITest):
    def datos(self, **extra):
        return {
            "especie": "perro",
            "descripcion": "Perro café con collar rojo",
            "lugar": "Plaza de Armas",
            "fecha_avistamiento": str(timezone.localdate()),
            **extra,
        }

    def reportar(self, user, **extra):
        self.client.force_authenticate(user)
        return self.client.post(URL, self.datos(**extra), format="multipart")

    def crear(self, user, **extra):
        return Avistamiento.objects.create(
            reportante=user, especie="perro", descripcion="Café", lugar="Plaza",
            fecha_avistamiento=timezone.localdate(), **extra
        )

    def accion(self, user, avistamiento, nombre, datos=None):
        self.client.force_authenticate(user)
        return self.client.post(f"{URL}{avistamiento.pk}/{nombre}/", datos, format="json")

    # --- reportar ---
    def test_adoptante_reporta_con_foto(self):
        response = self.reportar(self.adoptante, foto=imagen(), lat="-33.4489", lng="-70.6693")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["reportante"], self.adoptante.pk)
        self.assertEqual(response.data["estado"], "reportado")
        self.assertIsNone(response.data["animal"])

    def test_anonimo_no_reporta(self):
        self.assertEqual(self.client.post(URL, self.datos(), format="multipart").status_code, 401)

    def test_fecha_futura_se_rechaza(self):
        futuro = str(timezone.localdate() + timedelta(days=1))
        self.assertEqual(self.reportar(self.adoptante, fecha_avistamiento=futuro).status_code, 400)

    def test_coordenadas_fuera_de_rango(self):
        self.assertEqual(self.reportar(self.adoptante, lat="91").status_code, 400)
        self.assertEqual(self.reportar(self.adoptante, lng="-181").status_code, 400)

    def test_especie_invalida_y_foto_falsa(self):
        self.assertEqual(self.reportar(self.adoptante, especie="dragon").status_code, 400)
        falsa = SimpleUploadedFile("virus.png", b"no soy imagen", content_type="image/png")
        self.assertEqual(self.reportar(self.adoptante, foto=falsa).status_code, 400)

    # --- leer ---
    def test_adoptante_solo_ve_los_suyos_y_ajeno_da_404(self):
        propio = self.crear(self.adoptante)
        ajeno = self.crear(self.otro)
        self.client.force_authenticate(self.adoptante)
        self.assertEqual(self.client.get(URL).data["count"], 1)
        self.assertEqual(self.client.get(f"{URL}{propio.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"{URL}{ajeno.pk}/").status_code, 404)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(URL).data["count"], 2)

    # --- verificar / descartar ---
    def test_staff_verifica_y_descarta(self):
        a, b = self.crear(self.adoptante), self.crear(self.adoptante)
        self.assertEqual(self.accion(self.staff, a, "verificar").data["estado"], "verificado")
        self.assertEqual(self.accion(self.staff, b, "descartar").data["estado"], "descartado")

    def test_adoptante_no_verifica(self):
        self.assertEqual(self.accion(self.adoptante, self.crear(self.adoptante), "verificar").status_code, 403)

    def test_verificar_o_descartar_resuelto_responde_409(self):
        avistamiento = self.crear(self.adoptante)
        self.accion(self.staff, avistamiento, "verificar")
        self.assertEqual(self.accion(self.staff, avistamiento, "verificar").status_code, 409)
        self.assertEqual(self.accion(self.staff, avistamiento, "descartar").status_code, 409)

    # --- convertir ---
    def test_convertir_crea_animal_adoptable_y_enlaza(self):
        avistamiento = self.crear(self.adoptante, foto=imagen())
        self.accion(self.staff, avistamiento, "verificar")
        response = self.accion(self.staff, avistamiento, "convertir", {"nombre": "Canelo"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["nombre"], "Canelo")
        self.assertEqual(response.data["estado"], "adoptable")
        self.assertEqual(response.data["especie"], "perro")
        avistamiento.refresh_from_db()
        self.assertEqual(avistamiento.animal.pk, response.data["id"])
        self.assertEqual(avistamiento.animal.foto.name, avistamiento.foto.name)

    def test_convertir_sin_nombre_usa_uno_por_defecto(self):
        avistamiento = self.crear(self.adoptante)
        self.accion(self.staff, avistamiento, "verificar")
        response = self.accion(self.staff, avistamiento, "convertir")
        self.assertEqual(response.data["nombre"], f"Avistado #{avistamiento.pk}")

    def test_convertir_sin_verificar_responde_409(self):
        avistamiento = self.crear(self.adoptante)
        self.assertEqual(self.accion(self.staff, avistamiento, "convertir").status_code, 409)
        self.assertEqual(Animal.objects.count(), 0)

    def test_convertir_dos_veces_responde_409(self):
        avistamiento = self.crear(self.adoptante)
        self.accion(self.staff, avistamiento, "verificar")
        self.accion(self.staff, avistamiento, "convertir")
        self.assertEqual(self.accion(self.staff, avistamiento, "convertir").status_code, 409)
        self.assertEqual(Animal.objects.count(), 1)
