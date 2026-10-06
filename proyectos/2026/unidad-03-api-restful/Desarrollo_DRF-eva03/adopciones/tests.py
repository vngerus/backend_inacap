from adopciones.models import SolicitudAdopcion
from animales.models import Animal
from config.pruebas import BaseAPITest

URL = "/api/v1/solicitudes/"


class SolicitudesTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.animal = Animal.objects.create(nombre="Firulais", especie="perro")
        self.otro_animal = Animal.objects.create(nombre="Misu", especie="gato")

    def solicitar(self, user, animal=None):
        self.client.force_authenticate(user)
        return self.client.post(URL, {"animal": (animal or self.animal).pk, "mensaje": "Tengo patio"}, format="json")

    def crear(self, user, animal=None):
        return SolicitudAdopcion.objects.create(animal=animal or self.animal, usuario=user, mensaje="x")

    def accion(self, user, solicitud, nombre):
        self.client.force_authenticate(user)
        return self.client.post(f"{URL}{solicitud.pk}/{nombre}/")

    # --- crear ---
    def test_adoptante_crea_solicitud_pendiente_a_su_nombre(self):
        response = self.solicitar(self.adoptante)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["estado"], "pendiente")
        self.assertEqual(response.data["usuario"], self.adoptante.pk)

    def test_anonimo_no_crea(self):
        self.assertEqual(self.client.post(URL, {"animal": self.animal.pk, "mensaje": "x"}, format="json").status_code, 401)

    def test_animal_adoptado_responde_409(self):
        self.animal.estado = "adoptado"
        self.animal.save()
        self.assertEqual(self.solicitar(self.adoptante).status_code, 409)

    def test_solicitud_pendiente_duplicada_responde_400(self):
        self.solicitar(self.adoptante)
        self.assertEqual(self.solicitar(self.adoptante).status_code, 400)

    def test_puede_pedir_otro_animal_o_repetir_tras_cancelar(self):
        primera = self.solicitar(self.adoptante)
        self.assertEqual(self.solicitar(self.adoptante, self.otro_animal).status_code, 201)
        self.client.post(f"{URL}{primera.data['id']}/cancelar/")
        self.assertEqual(self.solicitar(self.adoptante).status_code, 201)

    # --- leer ---
    def test_adoptante_solo_ve_las_suyas_y_staff_ve_todas(self):
        propia = self.crear(self.adoptante)
        ajena = self.crear(self.otro, self.otro_animal)
        self.client.force_authenticate(self.adoptante)
        self.assertEqual(self.client.get(URL).data["count"], 1)
        self.assertEqual(self.client.get(f"{URL}{propia.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"{URL}{ajena.pk}/").status_code, 404)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(URL).data["count"], 2)

    def test_filtro_por_estado(self):
        self.crear(self.adoptante)
        self.crear(self.otro, self.otro_animal).cancelar()
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(URL, {"estado": "pendiente"}).data["count"], 1)

    def test_no_se_edita_ni_borra_por_la_api(self):
        solicitud = self.crear(self.adoptante)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(f"{URL}{solicitud.pk}/", {"estado": "aprobada"}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(f"{URL}{solicitud.pk}/").status_code, 405)

    # --- cancelar ---
    def test_dueno_cancela_su_solicitud(self):
        solicitud = self.crear(self.adoptante)
        response = self.accion(self.adoptante, solicitud, "cancelar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

    def test_cancelar_ajena(self):
        solicitud = self.crear(self.otro)
        self.assertEqual(self.accion(self.adoptante, solicitud, "cancelar").status_code, 404)
        self.assertEqual(self.accion(self.staff, solicitud, "cancelar").status_code, 403)

    def test_cancelar_resuelta_responde_409(self):
        solicitud = self.crear(self.adoptante)
        self.accion(self.staff, solicitud, "rechazar")
        self.assertEqual(self.accion(self.adoptante, solicitud, "cancelar").status_code, 409)

    # --- aprobar / rechazar ---
    def test_aprobar_adopta_al_animal_y_rechaza_las_demas(self):
        ganadora = self.crear(self.adoptante)
        perdedora = self.crear(self.otro)
        otra_cosa = self.crear(self.otro, self.otro_animal)
        response = self.accion(self.staff, ganadora, "aprobar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "aprobada")
        self.assertEqual(response.data["resuelta_por"], self.staff.pk)
        for obj in (self.animal, perdedora, otra_cosa):
            obj.refresh_from_db()
        self.assertEqual(self.animal.estado, "adoptado")
        self.assertEqual(perdedora.estado, "rechazada")
        self.assertEqual(otra_cosa.estado, "pendiente")  # otro animal: intacta

    def test_admin_tambien_aprueba(self):
        self.assertEqual(self.accion(self.admin, self.crear(self.adoptante), "aprobar").status_code, 200)

    def test_adoptante_no_aprueba_ni_rechaza(self):
        solicitud = self.crear(self.adoptante)
        self.assertEqual(self.accion(self.adoptante, solicitud, "aprobar").status_code, 403)
        self.assertEqual(self.accion(self.adoptante, solicitud, "rechazar").status_code, 403)

    def test_aprobar_resuelta_responde_409(self):
        solicitud = self.crear(self.adoptante)
        self.accion(self.staff, solicitud, "rechazar")
        self.assertEqual(self.accion(self.staff, solicitud, "aprobar").status_code, 409)

    def test_aprobar_si_el_animal_ya_fue_adoptado_responde_409(self):
        solicitud = self.crear(self.adoptante)
        self.animal.estado = "adoptado"
        self.animal.save()
        self.assertEqual(self.accion(self.staff, solicitud, "aprobar").status_code, 409)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "pendiente")  # la transacción no deja nada a medias

    def test_rechazar_no_adopta_al_animal(self):
        solicitud = self.crear(self.adoptante)
        response = self.accion(self.staff, solicitud, "rechazar")
        self.assertEqual(response.data["estado"], "rechazada")
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.estado, "adoptable")
