from config.pruebas import BaseAPITest


class ConfiguracionTests(BaseAPITest):
    def test_api_cerrada_por_defecto(self):
        self.assertEqual(self.client.get("/api/v1/").status_code, 401)

    def test_respuestas_son_json(self):
        self.client.force_authenticate(self.adoptante)
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_schema_openapi_publico(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)

    def test_schema_documenta_todos_los_recursos(self):
        response = self.client.get("/api/schema/", {"format": "json"})
        self.assertEqual(response.status_code, 200)
        rutas = response.json()["paths"]
        for ruta in (
            "/api/v1/animales/",
            "/api/v1/solicitudes/{id}/aprobar/",
            "/api/v1/avistamientos/{id}/convertir/",
            "/api/v1/auth/login/",
            "/api/v1/usuarios/",
        ):
            self.assertIn(ruta, rutas)

    def test_swagger_ui_disponible(self):
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
