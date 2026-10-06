# API RESTful de Adopción de Animales (Eval 3) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir una API RESTful con Django REST Framework (adopción de animales, avistamientos y solicitudes) que llegue a nivel "Destacado" en los 7 indicadores de la Escala de Apreciación Unidad 3.

**Architecture:** Proyecto Django independiente (`config`) con 4 apps por recurso: `cuentas` (registro, JWT, roles, usuarios), `animales`, `adopciones` y `avistamientos`. La lógica de negocio (transiciones de estado, aprobar atómico, convertir avistamiento) vive en métodos del modelo; las vistas solo orquestan. Permisos jerárquicos con `is_staff`/`is_superuser` de Django, sin modelo de roles propio.

**Tech Stack:** Django 5.2, djangorestframework, djangorestframework-simplejwt (con blacklist), django-filter, drf-spectacular, Pillow, python-dotenv, SQLite. Tests con `python manage.py test` (`APITestCase` de DRF).

**Spec:** Pauta `C:\Users\Angel Smith\Downloads\Escala_Apreciacion_Unidad_3_API_RESTful.pdf` (7 indicadores, 35% de la nota, desarrollo individual) más las decisiones del grill-me del 2026-10-06 resumidas en la sección "Decisiones de diseño" de este plan.

## Global Constraints

- El proyecto vive en `proyectos/2026/unidad-03-api-restful/Desarrollo_DRF-eva03/`; todas las rutas de este plan son relativas a esa carpeta, y los comandos se corren desde ella. Se trabaja en `main` (decisión del usuario); `Desarrollo_Django-eva01/` y `eva02` ya están evaluadas y no se tocan.
- Dependencias permitidas, ninguna más: `Django>=5.2,<5.3`, `djangorestframework`, `djangorestframework-simplejwt`, `django-filter`, `drf-spectacular`, `pillow`, `python-dotenv`. El `requirements.txt` va dentro del proyecto, no se toca el de la raíz.
- Base de datos SQLite; sin `docker-compose`.
- Rutas versionadas `/api/v1/`, recursos en plural y sin verbos; las acciones fuera de CRUD son `POST /<recurso>/{id}/<accion>/`.
- Códigos de respuesta fijos: 201 al crear, 400 validación, 401 sin token, 403 sin permiso, 404 no existe o ajeno, 409 conflicto de estado, 429 throttling.
- JWT: access 15 minutos, refresh 30 días con rotación y blacklist; `logout` invalida el refresh.
- Fotos: solo jpg/png/webp, máximo 5 MB, verificadas con Pillow, guardadas con nombre UUID.
- Secretos (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`) desde `.env`; `.env.example` va al repo, `.env` no.
- Permisos por defecto cerrados (`IsAuthenticated`); lo público se abre explícitamente.
- Cada task termina con `python manage.py test` en verde antes del commit. Los commits se hacen con `git add .` desde la carpeta del proyecto (el `.gitignore` de la raíz ya excluye `venv/`, `.env`, `*.sqlite3` y, desde la Task 0, `media/`).
- Textos de API y mensajes de error en español.

## Decisiones de diseño (del grill-me)

| Tema | Decisión |
|---|---|
| Roles | Adoptante < Staff (`is_staff`) < Admin (`is_superuser`). Staff crea/edita animales y resuelve solicitudes y avistamientos; solo admin borra animales y gestiona usuarios (promover staff, desactivar). El registro siempre crea adoptantes |
| Usuario | `User` por defecto de Django; email único y obligatorio; login por `username` |
| Solicitud | `pendiente` → `aprobada` / `rechazada` / `cancelada`. Solo se resuelve desde `pendiente`; aprobar es atómico (animal pasa a `adoptado`, las demás pendientes del animal quedan `rechazada`) |
| Animal | `estado`: `adoptable` / `adoptado`. Solo se solicita un animal `adoptable` |
| Avistamiento | `reportado` → `verificado` / `descartado`; staff lo convierte en `Animal` una sola vez |
| Auth | simplejwt, throttling 5/min en registro, login y refresh, validadores de contraseña, sin escalada de privilegios |
| API | Paginación 20, filtros, búsqueda, orden, Swagger en `/api/docs/`, errores estándar de DRF |

## Review Focus

Entradas que el spec insinúa y ningún test "feliz" cubre; cada una tiene su test en la task dueña.

1. Archivo con extensión válida pero contenido que no es imagen, imagen con extensión peligrosa (`.html`) o formato no permitido (GIF con extensión `.png`) → 400 (Task 3).
2. Refresh reutilizado tras la rotación, refresh de otro usuario en `logout`, y refresh tras `logout` → 401/400, nunca sesión viva (Task 1).
3. Solicitar un animal ya adoptado → 409; solicitud duplicada pendiente → 400; aprobar una solicitud ya resuelta → 409 (Task 4).
4. Un adoptante pidiendo una solicitud o avistamiento ajeno → 404, no 403 (no se revela que existe) (Tasks 4 y 5).
5. Fecha de avistamiento futura, latitud/longitud fuera de rango y convertir dos veces el mismo avistamiento → 400/400/409 (Task 5).

---

### Task 0: Scaffold, DRF configurado y seguridad base

**Indicador:** 1 (Configura DRF según documentación oficial) y base del 3.

**Files:**
- Create: `requirements.txt`, `.env.example`, `.env` (no versionado), `manage.py`, `config/` (generado por `startproject`), apps vacías `cuentas/`, `animales/`, `adopciones/`, `avistamientos/` (generadas por `startapp`)
- Modify: `config/settings.py`, `config/urls.py`, `../../../../.gitignore`
- Create: `config/pruebas.py`
- Test: `config/tests.py`

**Interfaces:**
- Produces: `config.pruebas.BaseAPITest` (limpia el cache en `setUp` y crea `self.adoptante` "ana", `self.otro` "beto", `self.staff` "sofia" `is_staff`, `self.admin` "admin" superusuario, todos con clave `CLAVE`), `config.pruebas.imagen(nombre="foto.png", formato="PNG")` → `SimpleUploadedFile`, `config.pruebas.MEDIA_TEMPORAL` (directorio temporal para `override_settings(MEDIA_ROOT=...)`), `config.pruebas.CLAVE`. En `config/urls.py` el `router = DefaultRouter()` donde las tasks siguientes hacen `router.register(...)`.

- [ ] **Step 1: Entorno virtual, dependencias y proyecto**

```bash
cd proyectos/2026/unidad-03-api-restful/Desarrollo_DRF-eva03
python -m venv venv
source venv/Scripts/activate
pip install "Django>=5.2,<5.3" djangorestframework djangorestframework-simplejwt django-filter drf-spectacular pillow python-dotenv
pip freeze > requirements.txt
django-admin startproject config .
python manage.py startapp cuentas
python manage.py startapp animales
python manage.py startapp adopciones
python manage.py startapp avistamientos
```

Expected: carpetas `config/`, `cuentas/`, `animales/`, `adopciones/`, `avistamientos/` y `manage.py` creados. Nota: `venv/` ya está ignorado por git desde la raíz.

- [ ] **Step 2: Secretos fuera del código**

Crear `.env.example`:

```
DJANGO_SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Copiar y generar una clave real (el `.env` no se versiona):

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Pegar la clave generada en `DJANGO_SECRET_KEY` dentro de `.env`.

Ignorar las fotos subidas (desde la carpeta del proyecto):

```bash
printf '\nmedia/\n' >> ../../../../.gitignore
```

- [ ] **Step 3: Escribir el test que falla**

Crear `config/pruebas.py`:

```python
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
```

Reemplazar `config/tests.py` por:

```python
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
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

Run: `python manage.py test config -v 2`
Expected: `FAIL`/`ERROR` — `/api/v1/` devuelve 404 (aún no hay rutas) o `KeyError: 'DJANGO_SECRET_KEY'` si falta el `.env`.

- [ ] **Step 5: Configurar `config/settings.py`**

Reemplazar el bloque inicial (imports, `BASE_DIR`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) por:

```python
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # sin valor por defecto: falla fuerte si falta
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
```

Agregar al final de `INSTALLED_APPS`:

```python
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "cuentas",
    "animales",
    "adopciones",
    "avistamientos",
```

Cambiar idioma y zona horaria:

```python
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
```

Agregar al final del archivo:

```python
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "120/min", "auth": "5/min"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API de Adopción de Animales",
    "DESCRIPTION": "Animales adoptables, solicitudes de adopción y avistamientos. Autenticación JWT.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,  # necesario para subir fotos (multipart) desde Swagger
}
```

- [ ] **Step 6: Configurar `config/urls.py`**

Reemplazar el contenido por:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # solo sirve con DEBUG=1
```

- [ ] **Step 7: Migrar y correr los tests**

Run: `python manage.py migrate && python manage.py test config -v 2`
Expected: `OK` (3 tests).

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: scaffold DRF con JWT, paginacion, throttling y secretos por .env"
```

---

### Task 1: Autenticación JWT (registro, login, refresh, logout)

**Indicadores:** 2 (autenticación) y 3 (seguridad en la autenticación).

**Files:**
- Create: `cuentas/throttles.py`, `cuentas/serializers.py`, `cuentas/views.py`, `cuentas/urls.py`
- Modify: `config/urls.py`
- Test: `cuentas/tests.py`

**Interfaces:**
- Consumes: `BaseAPITest`, `CLAVE` (Task 0).
- Produces: rutas `POST /api/v1/auth/{registro,login,refresh,logout}/`; `cuentas.throttles.AuthRateThrottle` (scope `auth`).

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar `cuentas/tests.py` por:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test cuentas -v 2`
Expected: `FAIL` — las rutas `/api/v1/auth/...` devuelven 404.

- [ ] **Step 3: Throttle propio para autenticación**

Crear `cuentas/throttles.py`:

```python
from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"  # 5/min por IP, definido en settings.DEFAULT_THROTTLE_RATES
```

- [ ] **Step 4: Serializers**

Crear `cuentas/serializers.py`:

```python
from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), lookup="iexact", message="Ya existe una cuenta con este email.")]
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")  # sin is_staff/is_superuser: nadie se auto-promueve

    def validate_password(self, value):
        password_validation.validate_password(value)  # usa AUTH_PASSWORD_VALIDATORS
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        error = serializers.ValidationError({"refresh": "Token inválido o expirado."})
        try:
            self.token = RefreshToken(attrs["refresh"])
        except TokenError:
            raise error
        if str(self.token["user_id"]) != str(self.context["request"].user.pk):
            raise error  # no se puede invalidar el token de otra persona
        return attrs

    def save(self):
        self.token.blacklist()
```

- [ ] **Step 5: Vistas y rutas**

Crear `cuentas/views.py`:

```python
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import LogoutSerializer, RegistroSerializer
from .throttles import AuthRateThrottle


class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]


class LoginView(TokenObtainPairView):
    throttle_classes = [AuthRateThrottle]


class RefreshView(TokenRefreshView):
    throttle_classes = [AuthRateThrottle]


class LogoutView(APIView):
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=205)
```

Crear `cuentas/urls.py`:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
```

En `config/urls.py`, agregar antes de la línea `path("api/v1/", include(router.urls)),`:

```python
    path("api/v1/auth/", include("cuentas.urls")),
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `python manage.py test -v 2`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: autenticacion JWT con registro, rotacion de refresh, logout y throttling"
```

---

### Task 2: Roles jerárquicos y gestión de usuarios (solo admin)

**Indicadores:** 2 y 3 (control de acceso, sin escalada de privilegios).

**Files:**
- Create: `cuentas/permissions.py`
- Modify: `cuentas/serializers.py`, `cuentas/views.py`, `config/urls.py`
- Modify: `cuentas/tests.py`

**Interfaces:**
- Consumes: `BaseAPITest` (Task 0), `LOGIN` (definido en `cuentas/tests.py`, Task 1).
- Produces: permisos `cuentas.permissions.IsStaff` (staff o superusuario), `cuentas.permissions.IsAdmin` (superusuario) — usados por las Tasks 3, 4 y 5; ruta `/api/v1/usuarios/` (GET lista/detalle, PATCH) solo admin.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `cuentas/tests.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test cuentas -v 2`
Expected: `FAIL` — `/api/v1/usuarios/` devuelve 404.

- [ ] **Step 3: Permisos**

Crear `cuentas/permissions.py`:

```python
from rest_framework.permissions import BasePermission


class IsStaff(BasePermission):
    """Staff o admin: la jerarquía es adoptante < staff < admin."""

    message = "Se requiere rol staff."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsAdmin(BasePermission):
    message = "Se requiere rol admin."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
```

- [ ] **Step 4: Serializer y vista de usuarios**

Agregar al final de `cuentas/serializers.py`:

```python
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff", "is_superuser", "is_active")
        read_only_fields = ("id", "username", "email", "is_superuser")  # admin solo cambia is_staff e is_active
```

En `cuentas/views.py`, ajustar los imports y agregar el viewset:

```python
from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, viewsets
```

(reemplaza la línea `from rest_framework import generics`), y agregar `from .permissions import IsAdmin` y `UsuarioSerializer` al import de serializers:

```python
from .permissions import IsAdmin
from .serializers import LogoutSerializer, RegistroSerializer, UsuarioSerializer
```

Al final del archivo:

```python
class UsuarioViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = get_user_model().objects.order_by("id")
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "patch", "head", "options"]  # sin PUT ni DELETE: se desactiva, no se borra
```

En `config/urls.py`, agregar el import y el registro del router:

```python
from cuentas.views import UsuarioViewSet
```

```python
router.register("usuarios", UsuarioViewSet, basename="usuario")
```

(el `register` va justo debajo de `router = DefaultRouter()`).

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `python manage.py test -v 2`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: roles jerarquicos y gestion de usuarios solo para admin"
```

---

### Task 3: Animales con fotos validadas

**Indicadores:** 4 (JSON), 5 (endpoints), 6 (RESTful) y 3 (validación de archivos).

**Files:**
- Create: `config/uploads.py`, `animales/serializers.py`, `animales/views.py`
- Modify: `animales/models.py`, `config/urls.py`
- Test: `animales/tests.py`

**Interfaces:**
- Consumes: `IsStaff`, `IsAdmin` (Task 2), `BaseAPITest`, `imagen`, `MEDIA_TEMPORAL` (Task 0).
- Produces: `config.uploads.foto_path` (upload_to con UUID), `config.uploads.validar_foto` y `config.uploads.MAX_FOTO_BYTES` (reutilizados por la Task 5); modelo `animales.models.Animal` con `Animal.Especie`, `Animal.Sexo`, `Animal.Estado` (`ADOPTABLE`, `ADOPTADO`); `animales.serializers.AnimalSerializer`; ruta `/api/v1/animales/`.

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar `animales/tests.py` por:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test animales -v 2`
Expected: `ERROR` — `ImportError: cannot import name 'Animal'` / `No module named 'config.uploads'`.

- [ ] **Step 3: Subida y validación de fotos**

Crear `config/uploads.py`:

```python
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
```

- [ ] **Step 4: Modelo**

Reemplazar `animales/models.py` por:

```python
from django.db import models

from config.uploads import foto_path, validar_foto


class Animal(models.Model):
    class Especie(models.TextChoices):
        PERRO = "perro", "Perro"
        GATO = "gato", "Gato"
        OTRO = "otro", "Otro"

    class Sexo(models.TextChoices):
        MACHO = "macho", "Macho"
        HEMBRA = "hembra", "Hembra"
        DESCONOCIDO = "desconocido", "Desconocido"

    class Estado(models.TextChoices):
        ADOPTABLE = "adoptable", "Adoptable"
        ADOPTADO = "adoptado", "Adoptado"

    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=10, choices=Especie.choices)
    sexo = models.CharField(max_length=12, choices=Sexo.choices, default=Sexo.DESCONOCIDO)
    edad_meses = models.PositiveIntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    foto = models.ImageField(upload_to=foto_path, blank=True, validators=[validar_foto])
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ADOPTABLE)
    refugio = models.CharField(max_length=100, blank=True)  # ponytail: texto; pasar a modelo si hace falta gestionar refugios
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado", "-id"]  # orden estable para la paginación

    def __str__(self):
        return self.nombre
```

Generar la migración:

Run: `python manage.py makemigrations animales`
Expected: `animales/migrations/0001_initial.py` creado.

- [ ] **Step 5: Serializer, vista y ruta**

Crear `animales/serializers.py`:

```python
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
```

Crear `animales/views.py`:

```python
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from cuentas.permissions import IsAdmin, IsStaff

from .models import Animal
from .serializers import AnimalSerializer


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    filterset_fields = ["especie", "sexo", "estado"]
    search_fields = ["nombre", "descripcion", "refugio"]
    ordering_fields = ["creado", "edad_meses", "nombre"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "destroy":
            return [IsAdmin()]
        return [IsStaff()]
```

En `config/urls.py`, agregar el import y el registro:

```python
from animales.views import AnimalViewSet
```

```python
router.register("animales", AnimalViewSet, basename="animal")
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `python manage.py test -v 2`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: CRUD de animales con roles, filtros y fotos validadas"
```

---

### Task 4: Solicitudes de adopción con ciclo de vida

**Indicadores:** 5 y 6 (endpoints y códigos de respuesta RESTful), 4 (JSON consistente).

**Files:**
- Create: `config/exceptions.py`, `adopciones/serializers.py`, `adopciones/views.py`
- Modify: `adopciones/models.py`, `config/urls.py`
- Test: `adopciones/tests.py`

**Interfaces:**
- Consumes: `Animal` (Task 3), `IsStaff` (Task 2), `BaseAPITest` (Task 0).
- Produces: `config.exceptions.Conflicto` (APIException 409, reutilizada por la Task 5); modelo `adopciones.models.SolicitudAdopcion` con `SolicitudAdopcion.Estado` y métodos `aprobar(por)`, `rechazar(por)`, `cancelar()`; ruta `/api/v1/solicitudes/` con acciones `aprobar`, `rechazar`, `cancelar`.

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar `adopciones/tests.py` por:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test adopciones -v 2`
Expected: `ERROR` — `ImportError: cannot import name 'SolicitudAdopcion'`.

- [ ] **Step 3: Excepción 409**

Crear `config/exceptions.py`:

```python
from rest_framework import status
from rest_framework.exceptions import APIException


class Conflicto(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflicto con el estado actual del recurso."
    default_code = "conflicto"
```

- [ ] **Step 4: Modelo con las reglas de negocio**

Reemplazar `adopciones/models.py` por:

```python
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from animales.models import Animal
from config.exceptions import Conflicto


class SolicitudAdopcion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"
        CANCELADA = "cancelada", "Cancelada"

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="solicitudes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solicitudes")
    mensaje = models.TextField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)
    resuelta = models.DateTimeField(null=True, blank=True)
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="solicitudes_resueltas"
    )

    class Meta:
        ordering = ["-creada", "-id"]
        constraints = [
            # respaldo en la base de datos de la regla "una pendiente por usuario y animal"
            models.UniqueConstraint(
                fields=["animal", "usuario"],
                condition=models.Q(estado="pendiente"),
                name="una_pendiente_por_usuario_y_animal",
            )
        ]

    def _resolver(self, estado, por=None):
        if self.estado != self.Estado.PENDIENTE:
            raise Conflicto("La solicitud ya fue resuelta.")
        self.estado = estado
        self.resuelta = timezone.now()
        self.resuelta_por = por
        self.save()

    def aprobar(self, por):
        with transaction.atomic():
            animal = Animal.objects.select_for_update().get(pk=self.animal_id)
            if animal.estado != Animal.Estado.ADOPTABLE:
                raise Conflicto("El animal ya fue adoptado.")
            self._resolver(self.Estado.APROBADA, por)
            animal.estado = Animal.Estado.ADOPTADO
            animal.save(update_fields=["estado"])
            SolicitudAdopcion.objects.filter(animal=animal, estado=self.Estado.PENDIENTE).update(
                estado=self.Estado.RECHAZADA, resuelta=timezone.now(), resuelta_por=por
            )

    def rechazar(self, por):
        self._resolver(self.Estado.RECHAZADA, por)

    def cancelar(self):
        self._resolver(self.Estado.CANCELADA)
```

Generar la migración (depende de `animales`):

Run: `python manage.py makemigrations adopciones`
Expected: `adopciones/migrations/0001_initial.py` creado.

- [ ] **Step 5: Serializer**

Crear `adopciones/serializers.py`:

```python
from rest_framework import serializers

from animales.models import Animal
from config.exceptions import Conflicto

from .models import SolicitudAdopcion


class SolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudAdopcion
        fields = ("id", "animal", "usuario", "mensaje", "estado", "creada", "resuelta", "resuelta_por")
        read_only_fields = ("id", "usuario", "estado", "creada", "resuelta", "resuelta_por")

    def validate_animal(self, animal):
        if animal.estado != Animal.Estado.ADOPTABLE:
            raise Conflicto("El animal ya fue adoptado.")
        return animal

    def validate(self, attrs):
        usuario = self.context["request"].user
        if SolicitudAdopcion.objects.filter(
            animal=attrs["animal"], usuario=usuario, estado=SolicitudAdopcion.Estado.PENDIENTE
        ).exists():
            raise serializers.ValidationError("Ya tienes una solicitud pendiente para este animal.")
        return attrs
```

- [ ] **Step 6: Vista, acciones y ruta**

Crear `adopciones/views.py`:

```python
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from cuentas.permissions import IsStaff

from .models import SolicitudAdopcion
from .serializers import SolicitudSerializer


class SolicitudViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = SolicitudSerializer
    filterset_fields = ["estado", "animal"]
    ordering_fields = ["creada"]

    def get_queryset(self):
        queryset = SolicitudAdopcion.objects.select_related("animal")
        if getattr(self, "swagger_fake_view", False):  # drf-spectacular genera el schema sin usuario
            return queryset.none()
        user = self.request.user
        # un adoptante no ve solicitudes ajenas: devuelve 404, no 403
        return queryset if (user.is_staff or user.is_superuser) else queryset.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def aprobar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.aprobar(request.user)
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def rechazar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.rechazar(request.user)
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        solicitud = self.get_object()
        if solicitud.usuario_id != request.user.id:
            raise PermissionDenied("Solo quien creó la solicitud puede cancelarla.")
        solicitud.cancelar()
        return Response(self.get_serializer(solicitud).data)
```

En `config/urls.py`, agregar el import y el registro:

```python
from adopciones.views import SolicitudViewSet
```

```python
router.register("solicitudes", SolicitudViewSet, basename="solicitud")
```

- [ ] **Step 7: Correr los tests y verificar que pasan**

Run: `python manage.py test -v 2`
Expected: `OK`. Si algún test de duplicados falla con un mensaje distinto de 400, revisar que no haya un `UniqueTogetherValidator` automático de DRF pisando el `validate()` explícito.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: solicitudes de adopcion con ciclo de vida y aprobacion atomica"
```

---

### Task 5: Avistamientos y conversión a animal

**Indicadores:** 5 y 6 (segundo recurso con acciones), 4 y 3 (validación de datos y fotos).

**Files:**
- Modify: `avistamientos/models.py`, `config/urls.py`
- Create: `avistamientos/serializers.py`, `avistamientos/views.py`
- Test: `avistamientos/tests.py`

**Interfaces:**
- Consumes: `Animal`, `AnimalSerializer` (Task 3), `Conflicto` (Task 4), `IsStaff` (Task 2), `foto_path`, `validar_foto` (Task 3), `imagen`, `MEDIA_TEMPORAL` (Task 0).
- Produces: modelo `avistamientos.models.Avistamiento` con `Avistamiento.Estado` y métodos `verificar()`, `descartar()`, `convertir(nombre="")` → `Animal`; ruta `/api/v1/avistamientos/` con acciones `verificar`, `descartar`, `convertir`.

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar `avistamientos/tests.py` por:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test avistamientos -v 2`
Expected: `ERROR` — `ImportError: cannot import name 'Avistamiento'`.

- [ ] **Step 3: Modelo**

Reemplazar `avistamientos/models.py` por:

```python
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from animales.models import Animal
from config.exceptions import Conflicto
from config.uploads import foto_path, validar_foto


class Avistamiento(models.Model):
    class Estado(models.TextChoices):
        REPORTADO = "reportado", "Reportado"
        VERIFICADO = "verificado", "Verificado"
        DESCARTADO = "descartado", "Descartado"

    reportante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avistamientos")
    especie = models.CharField(max_length=10, choices=Animal.Especie.choices)
    descripcion = models.TextField()
    lugar = models.CharField(max_length=200)
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    foto = models.ImageField(upload_to=foto_path, blank=True, validators=[validar_foto])
    fecha_avistamiento = models.DateField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.REPORTADO)
    animal = models.OneToOneField(Animal, on_delete=models.SET_NULL, null=True, blank=True, related_name="avistamiento")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado", "-id"]

    def _resolver(self, estado):
        if self.estado != self.Estado.REPORTADO:
            raise Conflicto("El avistamiento ya fue resuelto.")
        self.estado = estado
        self.save(update_fields=["estado"])

    def verificar(self):
        self._resolver(self.Estado.VERIFICADO)

    def descartar(self):
        self._resolver(self.Estado.DESCARTADO)

    def convertir(self, nombre=""):
        with transaction.atomic():
            if self.animal_id:
                raise Conflicto("El avistamiento ya fue convertido en animal.")
            if self.estado != self.Estado.VERIFICADO:
                raise Conflicto("Solo se convierten avistamientos verificados.")
            self.animal = Animal.objects.create(
                nombre=nombre or f"Avistado #{self.pk}",
                especie=self.especie,
                descripcion=self.descripcion,
                foto=self.foto.name,  # ponytail: comparte el archivo, no lo duplica
            )
            self.save(update_fields=["animal"])
        return self.animal
```

Generar la migración:

Run: `python manage.py makemigrations avistamientos`
Expected: `avistamientos/migrations/0001_initial.py` creado.

- [ ] **Step 4: Serializer**

Crear `avistamientos/serializers.py`:

```python
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
```

- [ ] **Step 5: Vista, acciones y ruta**

Crear `avistamientos/views.py`:

```python
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from animales.serializers import AnimalSerializer
from cuentas.permissions import IsStaff

from .models import Avistamiento
from .serializers import AvistamientoSerializer, ConvertirSerializer


class AvistamientoViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = AvistamientoSerializer
    filterset_fields = ["estado", "especie"]
    ordering_fields = ["creado", "fecha_avistamiento"]

    def get_queryset(self):
        queryset = Avistamiento.objects.all()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        user = self.request.user
        return queryset if (user.is_staff or user.is_superuser) else queryset.filter(reportante=user)

    def perform_create(self, serializer):
        serializer.save(reportante=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def verificar(self, request, pk=None):
        avistamiento = self.get_object()
        avistamiento.verificar()
        return Response(self.get_serializer(avistamiento).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def descartar(self, request, pk=None):
        avistamiento = self.get_object()
        avistamiento.descartar()
        return Response(self.get_serializer(avistamiento).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff], serializer_class=ConvertirSerializer)
    def convertir(self, request, pk=None):
        avistamiento = self.get_object()
        entrada = ConvertirSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        animal = avistamiento.convertir(entrada.validated_data.get("nombre", ""))
        return Response(AnimalSerializer(animal, context={"request": request}).data, status=status.HTTP_201_CREATED)
```

En `config/urls.py`, agregar el import y el registro:

```python
from avistamientos.views import AvistamientoViewSet
```

```python
router.register("avistamientos", AvistamientoViewSet, basename="avistamiento")
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `python manage.py test -v 2`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: avistamientos con verificacion y conversion a animal"
```

---

### Task 6: Documentación, evidencia de IA y verificación final

**Indicadores:** 1 (documentación de configuración), 7 (uso crítico de IA) y cierre de los productos esperados 9, 10 y 11 de la pauta.

**Files:**
- Create: `README.md`, `requests.http`
- Modify: `docs/uso-ia.md` (ya creado con las decisiones del grill-me; completar con lo que aparezca al implementar), `CLAUDE.md` (ya creado)
- Modify: `config/tests.py`
- Modify: `../../../../README.md` (estructura del repo con la unidad 3)

**Interfaces:**
- Consumes: todas las rutas anteriores.
- Produces: README ejecutable de principio a fin, colección `requests.http`, schema OpenAPI completo.

- [ ] **Step 1: Test de que el schema documenta todos los recursos**

Agregar al final de `config/tests.py`:

```python
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
```

Run: `python manage.py test config -v 2`
Expected: `OK`. Si falla por una ruta ausente o por una excepción de drf-spectacular al generar el schema, corregir el serializer o la vista indicados en el error (suele ser un `serializer_class` faltante en una `APIView` o `@action`) y repetir.

- [ ] **Step 2: Crear `requests.http`**

Crear `requests.http` (se ejecuta con la extensión REST Client de VS Code):

```http
@base = http://localhost:8000/api/v1

### Registrar adoptante
POST {{base}}/auth/registro/
Content-Type: application/json

{"username": "ana", "email": "ana@correo.cl", "password": "Clave-Segura-123"}

### Login (guarda los tokens)
# @name login
POST {{base}}/auth/login/
Content-Type: application/json

{"username": "ana", "password": "Clave-Segura-123"}

###
@access = {{login.response.body.access}}
@refresh = {{login.response.body.refresh}}

### Renovar access (rota el refresh)
POST {{base}}/auth/refresh/
Content-Type: application/json

{"refresh": "{{refresh}}"}

### Logout (invalida el refresh)
POST {{base}}/auth/logout/
Authorization: Bearer {{access}}
Content-Type: application/json

{"refresh": "{{refresh}}"}

### Listar animales adoptables (público)
GET {{base}}/animales/?estado=adoptable&especie=perro&search=firulais&ordering=-creado

### Solicitar adopción (autenticado)
POST {{base}}/solicitudes/
Authorization: Bearer {{access}}
Content-Type: application/json

{"animal": 1, "mensaje": "Tengo patio y tiempo"}

### Mis solicitudes
GET {{base}}/solicitudes/
Authorization: Bearer {{access}}

### Cancelar solicitud
POST {{base}}/solicitudes/1/cancelar/
Authorization: Bearer {{access}}

### Reportar avistamiento con foto
POST {{base}}/avistamientos/
Authorization: Bearer {{access}}
Content-Type: multipart/form-data; boundary=limite

--limite
Content-Disposition: form-data; name="especie"

perro
--limite
Content-Disposition: form-data; name="descripcion"

Perro café con collar rojo
--limite
Content-Disposition: form-data; name="lugar"

Plaza de Armas
--limite
Content-Disposition: form-data; name="fecha_avistamiento"

2026-10-06
--limite
Content-Disposition: form-data; name="foto"; filename="perro.png"
Content-Type: image/png

< ./perro.png
--limite--

### --- Solo staff: reemplazar {{access}} por el token de una cuenta staff ---

### Aprobar solicitud
POST {{base}}/solicitudes/1/aprobar/
Authorization: Bearer {{access}}

### Verificar avistamiento
POST {{base}}/avistamientos/1/verificar/
Authorization: Bearer {{access}}

### Convertir avistamiento en animal
POST {{base}}/avistamientos/1/convertir/
Authorization: Bearer {{access}}
Content-Type: application/json

{"nombre": "Canelo"}

### --- Solo admin ---

### Promover a staff
PATCH {{base}}/usuarios/2/
Authorization: Bearer {{access}}
Content-Type: application/json

{"is_staff": true}
```

- [ ] **Step 3: Crear `README.md`**

Crear `README.md`:

````markdown
# API de Adopción de Animales (Django REST Framework)

Evaluación 3 — Unidad 3 "Aplicación API RESTful" (INACAP, TI3V41). API REST con autenticación JWT para publicar animales adoptables, solicitar su adopción y reportar avistamientos de animales en la calle.

## 1. Instalar

Requiere Python 3.11 o superior.

```bash
cd proyectos/2026/unidad-03-api-restful/Desarrollo_DRF-eva03
python -m venv venv
source venv/Scripts/activate        # Windows (Git Bash). Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configurar

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Pega la clave generada en `DJANGO_SECRET_KEY` dentro de `.env`. Variables:

| Variable | Para qué | Ejemplo |
|---|---|---|
| `DJANGO_SECRET_KEY` | firma de tokens y sesiones (obligatoria) | clave aleatoria larga |
| `DJANGO_DEBUG` | `1` en desarrollo (también sirve las fotos), `0` en producción | `1` |
| `DJANGO_ALLOWED_HOSTS` | hosts permitidos, separados por coma | `localhost,127.0.0.1` |

```bash
python manage.py migrate
python manage.py createsuperuser     # este usuario es el rol Admin
```

## 3. Ejecutar

```bash
python manage.py runserver
```

- Documentación interactiva (Swagger): http://localhost:8000/api/docs/
- Schema OpenAPI: http://localhost:8000/api/schema/
- Colección de pruebas manuales: `requests.http` (extensión REST Client de VS Code)

## 4. Pruebas automáticas

```bash
python manage.py test
```

Cubren autenticación, permisos por rol, ciclo de solicitudes, validación de fotos y conversión de avistamientos.

## 5. Roles

| Rol | Cómo se obtiene | Puede |
|---|---|---|
| Adoptante | registro público | ver animales, solicitar adopción, ver y cancelar sus solicitudes, reportar avistamientos y ver los suyos |
| Staff | un admin lo promueve (`is_staff`) | lo anterior, más crear/editar animales, aprobar/rechazar solicitudes, verificar/descartar/convertir avistamientos y ver todo |
| Admin | `createsuperuser` | lo anterior, más borrar animales y gestionar usuarios (`/usuarios/`: promover a staff, desactivar cuentas) |

## 6. Endpoints (`/api/v1/`)

| Método y ruta | Acceso | Códigos |
|---|---|---|
| `POST auth/registro/` | público | 201, 400, 429 |
| `POST auth/login/` | público | 200, 401, 429 |
| `POST auth/refresh/` | público | 200, 401, 429 |
| `POST auth/logout/` | autenticado | 205, 400, 401 |
| `GET animales/` (filtros `especie`, `sexo`, `estado`; `search`; `ordering`) | público | 200 |
| `GET animales/{id}/` | público | 200, 404 |
| `POST animales/`, `PATCH/PUT animales/{id}/` | staff | 201/200, 400, 401, 403 |
| `DELETE animales/{id}/` | admin | 204, 403 |
| `POST solicitudes/` | autenticado | 201, 400 (duplicada), 409 (animal adoptado) |
| `GET solicitudes/`, `GET solicitudes/{id}/` | dueño o staff | 200, 404 |
| `POST solicitudes/{id}/cancelar/` | dueño | 200, 403, 404, 409 |
| `POST solicitudes/{id}/aprobar/`, `rechazar/` | staff | 200, 403, 404, 409 |
| `POST avistamientos/` (multipart, con foto) | autenticado | 201, 400 |
| `GET avistamientos/`, `GET avistamientos/{id}/` | dueño o staff | 200, 404 |
| `POST avistamientos/{id}/verificar/`, `descartar/` | staff | 200, 403, 404, 409 |
| `POST avistamientos/{id}/convertir/` | staff | 201, 403, 404, 409 |
| `GET usuarios/`, `GET/PATCH usuarios/{id}/` | admin | 200, 403 |

Listados paginados (20 por página): `{"count", "next", "previous", "results"}`. Errores en el formato estándar de DRF: `{"detail": "..."}` o `{"campo": ["mensaje"]}`.

### Reglas de negocio

- Una solicitud pasa de `pendiente` a `aprobada`, `rechazada` o `cancelada`, y ya no cambia.
- Aprobar una solicitud es atómico: el animal pasa a `adoptado` y las demás solicitudes pendientes de ese animal quedan `rechazada`.
- Solo se solicita un animal `adoptable`; un usuario no puede tener dos solicitudes pendientes para el mismo animal.
- Un avistamiento `verificado` se convierte en un `Animal` adoptable una sola vez.

### Ejemplo rápido

```bash
curl -X POST http://localhost:8000/api/v1/auth/registro/ -H "Content-Type: application/json" \
  -d '{"username":"ana","email":"ana@correo.cl","password":"Clave-Segura-123"}'
curl -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" \
  -d '{"username":"ana","password":"Clave-Segura-123"}'
curl http://localhost:8000/api/v1/solicitudes/ -H "Authorization: Bearer <access>"
```

## 7. Seguridad aplicada

1. **JWT con refresh rotativo y blacklist**: access de 15 minutos, refresh de 30 días que se renueva solo mientras se usa. Cada refresh se usa una vez; `logout` lo invalida. No hay sesión única ni OTP (fuera de alcance).
2. **Throttling**: 5 intentos por minuto por IP en registro, login y refresh; 60/min anónimos y 120/min autenticados en el resto.
3. **Contraseñas** validadas con `AUTH_PASSWORD_VALIDATORS` de Django al registrarse.
4. **Secretos** en `.env` (no versionado); la app no arranca sin `DJANGO_SECRET_KEY`.
5. **Permisos cerrados por defecto** (`IsAuthenticated`); los endpoints públicos se abren explícitamente.
6. **Sin escalada de privilegios**: el registro ignora `is_staff`/`is_superuser`; solo un admin cambia roles y `is_superuser` no se puede modificar por la API.
7. **Login sin pistas**: el mismo error si falla el usuario o la clave.
8. **Fotos**: solo jpg/png/webp, máximo 5 MB, contenido verificado con Pillow, guardadas con nombre UUID.
9. **Recursos ajenos**: un adoptante que pide una solicitud o avistamiento de otra persona recibe 404.
10. **Respuestas solo JSON**: sin API navegable de DRF en producción.

Pendiente para un despliegue real (no exigido por la pauta): HTTPS (`SECURE_SSL_REDIRECT`, HSTS, cookies seguras), servir `media/` desde un servidor de archivos y almacenamiento externo para las fotos.

## 8. Uso de IA

El plan de implementación, el diseño de la API y la mayor parte del código se hicieron con apoyo de una IA (Claude). Cada decisión relevante, qué recomendó la IA, cómo se verificó y qué se cambió está en `docs/uso-ia.md`. El plan está en `docs/superpowers/plans/2026-10-06-cumplir-pauta-eva3.md`.
````

- [ ] **Step 4: Revisar y completar `docs/uso-ia.md`**

Abrir `docs/uso-ia.md` y verificar entrada por entrada:
- Que cada "Cómo lo verifiqué" apunte a un test que existe (`python manage.py test -v 2` lista los nombres).
- Agregar una entrada por cada problema real que apareció al ejecutar este plan (error de drf-spectacular, validador duplicado de DRF, etc.), con los cuatro campos.
- Reescribir con las palabras propias lo que no suene a decisión personal: el corrector evalúa criterio, no volumen.

- [ ] **Step 5: Actualizar el README principal del repo**

En `../../../../README.md`, agregar `unidad-03-api-restful/Desarrollo_DRF-eva03/` al diagrama de estructura y una línea `cd` para entrar a ese proyecto, siguiendo el estilo de las unidades 1 y 2.

- [ ] **Step 6: Verificación final**

Run: `python manage.py test -v 2`
Expected: `OK`, todos los tests en verde.

Run: `python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

Run: `DJANGO_DEBUG=0 python manage.py check --deploy`
Expected: solo avisos de HTTPS/HSTS/cookies seguras (documentados como pendientes en el README); ningún aviso de `SECRET_KEY` ni de `DEBUG`.

Prueba manual con `runserver`: abrir http://localhost:8000/api/docs/, registrarse, hacer login, usar "Authorize" con el access token y ejecutar `GET /solicitudes/`.

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "docs: README, requests.http, evidencia de uso de IA y verificacion final"
```
