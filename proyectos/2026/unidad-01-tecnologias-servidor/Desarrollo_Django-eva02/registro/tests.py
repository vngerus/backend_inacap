from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Dueno, Michi

# Datos de prueba generados con apoyo de IA (variados por tipo/pelaje),
# validados aquí antes de usarse como fixture de demo.
DATOS_PRUEBA = [
    {"nombre": "Luna", "tipo": "calico"},
    {"nombre": "Kimchi", "tipo": "naranja"},
    {"nombre": "Lea", "tipo": "tuxedo"},
    {"nombre": "Nube", "tipo": "blanco"},
    {"nombre": "Tigre", "tipo": "atigrado"},
]


class MichiModelTests(TestCase):
    def test_str_devuelve_nombre(self):
        michi = Michi.objects.create(nombre="Luna", tipo="calico")
        self.assertEqual(str(michi), "Luna")

    def test_datos_prueba_son_validos(self):
        for dato in DATOS_PRUEBA:
            michi = Michi(**dato)
            michi.full_clean()  # valida max_length y campos requeridos
            michi.save()
        self.assertEqual(Michi.objects.count(), len(DATOS_PRUEBA))

    def test_relacion_dueno_michis(self):
        dueno = Dueno.objects.create(nombre="Ana", telefono="+56911111111")
        Michi.objects.create(nombre="Luna", tipo="calico", dueno=dueno)
        Michi.objects.create(nombre="Kimchi", tipo="naranja", dueno=dueno)
        self.assertEqual(dueno.michis.count(), 2)

    def test_michi_sin_dueno_es_valido(self):
        michi = Michi.objects.create(nombre="Nube", tipo="blanco")
        self.assertIsNone(michi.dueno)


class RegistroViewsTests(TestCase):
    def setUp(self):
        self.michi = Michi.objects.create(nombre="Luna", tipo="calico")
        user = User.objects.create_user(username='ana', password='clave-segura-123')
        self.client.force_login(user)

    def test_lista_michis_ok(self):
        response = self.client.get(reverse('lista_michis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Luna")

    def test_detalle_michi_ok(self):
        response = self.client.get(reverse('detalle_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 200)

    def test_agregar_michi_post(self):
        response = self.client.post(reverse('agregar_michi'), {
            'nombre': 'Kimchi',
            'tipo': 'naranja',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Michi.objects.filter(nombre='Kimchi').exists())

    def test_editar_michi_post(self):
        response = self.client.post(
            reverse('editar_michi', args=(self.michi.id,)),
            {'nombre': 'Luna', 'tipo': 'blanco y negro'},
        )
        self.assertEqual(response.status_code, 302)
        self.michi.refresh_from_db()
        self.assertEqual(self.michi.tipo, 'blanco y negro')

    def test_eliminar_michi_post(self):
        response = self.client.post(reverse('eliminar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Michi.objects.filter(id=self.michi.id).exists())

    def test_eliminar_michi_get_muestra_confirmacion(self):
        response = self.client.get(reverse('eliminar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.michi.nombre)



class AutenticacionTests(TestCase):
    def setUp(self):
        self.michi = Michi.objects.create(nombre="Luna", tipo="calico")
        self.user = User.objects.create_user(username='ana', password='clave-segura-123')

    def test_anonimo_no_puede_agregar(self):
        response = self.client.get(reverse('agregar_michi'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_anonimo_no_puede_editar(self):
        response = self.client.get(reverse('editar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_anonimo_no_puede_eliminar(self):
        response = self.client.post(reverse('eliminar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_usuario_autenticado_puede_agregar(self):
        self.client.login(username='ana', password='clave-segura-123')
        response = self.client.get(reverse('agregar_michi'))
        self.assertEqual(response.status_code, 200)

    def test_login_logout_flow(self):
        response = self.client.post(reverse('login'), {
            'username': 'ana', 'password': 'clave-segura-123',
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
