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

Cubren autenticación, permisos por rol, ciclo de solicitudes, validación de fotos, conversión de avistamientos y que el schema OpenAPI documente todos los recursos.

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
10. **Respuestas solo JSON**: sin API navegable de DRF.

Pendiente para un despliegue real (no exigido por la pauta): HTTPS (`SECURE_SSL_REDIRECT`, HSTS, cookies seguras), servir `media/` desde un servidor de archivos y almacenamiento externo para las fotos.

## 8. Uso de IA

El plan de implementación, el diseño de la API y la mayor parte del código se hicieron con apoyo de una IA (Claude). Cada decisión relevante, qué recomendó la IA, cómo se verificó y qué se cambió está en `docs/uso-ia.md`. El plan está en `docs/superpowers/plans/2026-10-06-cumplir-pauta-eva3.md`.
