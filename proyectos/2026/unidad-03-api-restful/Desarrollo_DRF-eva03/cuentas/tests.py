from django.contrib.auth import get_user_model

from config.pruebas import CLAVE, BaseAPITest

User = get_user_model()
REGISTRO = "/api/v1/auth/registro/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"


class RegistroTests(BaseAPITest):
    def registrar(self, **extra):
        datos = {"username": "nuevo", "email": "nuevo@x.cl", "password": CLAVE, **extra}
        return self.client.post(REGISTRO, datos, format="json")

    def test_registro_crea_adoptante_sin_exponer_password(self):
        response = self.registrar()
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        user = User.objects.get(username="nuevo")
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertTrue(user.check_password(CLAVE))

    def test_registro_ignora_intento_de_escalada(self):
        response = self.registrar(is_staff=True, is_superuser=True)
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="nuevo")
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_registro_exige_email(self):
        response = self.client.post(REGISTRO, {"username": "x", "password": CLAVE}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_registro_rechaza_email_duplicado(self):
        response = self.registrar(email="ANA@x.cl")  # mismo email que ana, otra capitalización
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_registro_rechaza_password_debil(self):
        response = self.registrar(password="123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)


class LoginTests(BaseAPITest):
    def login(self, username="ana", password=CLAVE):
        return self.client.post(LOGIN, {"username": username, "password": password}, format="json")

    def test_login_devuelve_par_de_tokens(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_no_revela_si_falla_usuario_o_clave(self):
        usuario_malo = self.login(username="fantasma")
        clave_mala = self.login(password="otra-clave-mala")
        self.assertEqual(usuario_malo.status_code, 401)
        self.assertEqual(clave_mala.status_code, 401)
        self.assertEqual(usuario_malo.data, clave_mala.data)

    def test_login_tiene_throttling(self):
        codigos = [self.login(password="mala").status_code for _ in range(6)]
        self.assertEqual(codigos[:5], [401] * 5)
        self.assertEqual(codigos[5], 429)


class RefreshLogoutTests(BaseAPITest):
    def tokens(self, username="ana"):
        response = self.client.post(LOGIN, {"username": username, "password": CLAVE}, format="json")
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_refresh_rota_y_el_token_viejo_deja_de_servir(self):
        tokens = self.tokens()
        nuevo = self.client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(nuevo.status_code, 200)
        self.assertNotEqual(nuevo.data["refresh"], tokens["refresh"])
        reuso = self.client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(reuso.status_code, 401)

    def test_logout_invalida_el_refresh(self):
        tokens = self.tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(self.client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json").status_code, 205)
        self.client.credentials()
        self.assertEqual(self.client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json").status_code, 401)

    def test_logout_exige_autenticacion(self):
        tokens = self.tokens()
        self.assertEqual(self.client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json").status_code, 401)

    def test_logout_rechaza_token_invalido(self):
        self.client.force_authenticate(self.adoptante)
        self.assertEqual(self.client.post(LOGOUT, {"refresh": "no-es-un-token"}, format="json").status_code, 400)

    def test_logout_no_acepta_refresh_de_otro_usuario(self):
        ajeno = self.tokens("beto")
        propio = self.tokens("ana")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {propio['access']}")
        self.assertEqual(self.client.post(LOGOUT, {"refresh": ajeno["refresh"]}, format="json").status_code, 400)


class UsuariosAdminTests(BaseAPITest):
    def url(self, user):
        return f"/api/v1/usuarios/{user.pk}/"

    def test_solo_admin_ve_usuarios(self):
        self.assertEqual(self.client.get("/api/v1/usuarios/").status_code, 401)
        for user in (self.adoptante, self.staff):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get("/api/v1/usuarios/").status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/usuarios/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 4)

    def test_admin_promueve_a_staff(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url(self.adoptante), {"is_staff": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.adoptante.refresh_from_db()
        self.assertTrue(self.adoptante.is_staff)

    def test_staff_no_puede_promover_a_nadie(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(self.url(self.adoptante), {"is_staff": True}, format="json")
        self.assertEqual(response.status_code, 403)
        self.adoptante.refresh_from_db()
        self.assertFalse(self.adoptante.is_staff)

    def test_nadie_se_hace_superusuario_por_la_api(self):
        self.client.force_authenticate(self.admin)
        self.client.patch(self.url(self.adoptante), {"is_superuser": True}, format="json")
        self.adoptante.refresh_from_db()
        self.assertFalse(self.adoptante.is_superuser)

    def test_admin_desactiva_cuenta_y_ya_no_puede_entrar(self):
        self.client.force_authenticate(self.admin)
        self.client.patch(self.url(self.adoptante), {"is_active": False}, format="json")
        self.client.force_authenticate(None)
        response = self.client.post(LOGIN, {"username": "ana", "password": CLAVE}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_no_se_borran_usuarios_por_la_api(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(self.url(self.adoptante)).status_code, 405)
