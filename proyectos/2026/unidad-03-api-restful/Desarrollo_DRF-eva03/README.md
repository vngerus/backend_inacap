# API de Adopción de Animales

**Evaluación 3 — Unidad 3: Aplicación API RESTful** (INACAP, TI3V41 — Desarrollo de aplicaciones del lado del servidor). Desarrollo individual, 35 % de la nota. Tecnología principal: Python y Django REST Framework.

## Qué es

Una API REST para un refugio de animales. Permite:

- **Publicar animales** adoptables, con foto.
- **Solicitar su adopción**, con un ciclo de vida de la solicitud (pendiente, aprobada, rechazada, cancelada).
- **Reportar avistamientos** de animales en la calle, que el staff verifica y puede convertir en un animal adoptable.

La API responde siempre en JSON, se autentica con JWT y distingue tres roles (adoptante, staff y admin). Está documentada en Swagger.

## Qué pedía la evaluación y dónde se cumple

**Aprendizaje esperado 3.1:** desarrollar una API RESTful con Django REST Framework, aplicando autenticación, respuestas JSON y principios RESTful, considerando recomendaciones de seguridad y usando IA como apoyo.

| # | Indicador de la pauta (peso) | Dónde se cumple |
|---|---|---|
| 1 | Configura DRF según la documentación oficial (15 %) | `config/settings.py` (`REST_FRAMEWORK`, `SIMPLE_JWT`, `SPECTACULAR_SETTINGS`); una app por recurso: `cuentas`, `animales`, `adopciones`, `avistamientos`; secretos en `.env` |
| 2 | Implementa autenticación (20 %) | `cuentas/`: registro, login, refresh y logout con JWT; roles adoptante, staff y admin |
| 3 | Aplica recomendaciones de seguridad en la autenticación (15 %) | Sección [Seguridad](#seguridad-indicador-3) |
| 4 | Genera respuestas JSON (15 %) | Renderer solo JSON, listados paginados y errores con un único formato |
| 5 | Implementa los endpoints requeridos (15 %) | Sección [Endpoints](#endpoints-apiv1) |
| 6 | Implementa una API con características RESTful (10 %) | Rutas versionadas `/api/v1/`, recursos en plural, métodos HTTP y códigos de respuesta correctos |
| 7 | Utiliza IA de forma crítica y responsable (10 %) | [`docs/uso-ia.md`](docs/uso-ia.md) |

### Productos esperados

| Producto | Dónde está |
|---|---|
| Proyecto Django funcional | Este proyecto (`manage.py`, `config/`) |
| DRF correctamente configurado | `config/settings.py` |
| Al menos un recurso expuesto por API | Animales, solicitudes de adopción y avistamientos |
| Endpoints funcionales | [Endpoints](#endpoints-apiv1) y Swagger en `/api/docs/` |
| Respuestas en JSON | Todas; el renderer por defecto es solo JSON |
| Operaciones HTTP según el requerimiento | GET, POST, PATCH/PUT y DELETE según el recurso |
| Mecanismo de autenticación | JWT con `djangorestframework-simplejwt` |
| Medidas de seguridad aplicadas | [Seguridad](#seguridad-indicador-3) |
| Pruebas de los endpoints | 68 tests automáticos (`python manage.py test`) y `requests.http` |
| Evidencia del uso de IA y validación | [`docs/uso-ia.md`](docs/uso-ia.md) y el plan en `docs/superpowers/plans/` |
| README con instalar, configurar y ejecutar | Este archivo |

## Instalar, configurar y ejecutar

Requiere Python 3.11 o superior.

```bash
cd proyectos/2026/unidad-03-api-restful/Desarrollo_DRF-eva03
python -m venv venv
source venv/Scripts/activate         # Windows (Git Bash). Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                 # luego pon una clave real en DJANGO_SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"

python manage.py migrate
python manage.py createsuperuser     # este usuario es el rol Admin
python manage.py runserver
```

La app no arranca sin `DJANGO_SECRET_KEY` (a propósito, para no usar una clave por defecto).

| Variable de `.env` | Para qué | Ejemplo |
|---|---|---|
| `DJANGO_SECRET_KEY` | firma de tokens (obligatoria) | clave aleatoria larga |
| `DJANGO_DEBUG` | `1` en desarrollo (también sirve las fotos), `0` en producción | `1` |
| `DJANGO_ALLOWED_HOSTS` | hosts permitidos, separados por coma | `localhost,127.0.0.1` |

Con el servidor corriendo:

- Swagger (documentación y pruebas interactivas): http://localhost:8000/api/docs/
- Schema OpenAPI: http://localhost:8000/api/schema/
- Colección de pruebas manuales: `requests.http` (extensión REST Client de VS Code)

### Pruebas automáticas

```bash
python manage.py test
```

Cubren autenticación y rotación de tokens, permisos por rol, el ciclo de las solicitudes, la validación de fotos, la conversión de avistamientos y que el schema OpenAPI documente todos los recursos.

## Roles

| Rol | Cómo se obtiene | Puede |
|---|---|---|
| Adoptante | registro público | ver animales, solicitar adopción, ver y cancelar sus solicitudes, reportar avistamientos y ver los suyos |
| Staff | un admin lo promueve (`is_staff`) | lo anterior, más crear y editar animales, aprobar y rechazar solicitudes, verificar, descartar y convertir avistamientos, y ver todo |
| Admin | `createsuperuser` | lo anterior, más borrar animales y gestionar usuarios (`/usuarios/`: promover a staff, desactivar cuentas) |

## Endpoints (`/api/v1/`)

| Método y ruta | Acceso | Códigos |
|---|---|---|
| `POST auth/registro/` | público | 201, 400, 429 |
| `POST auth/login/` | público | 200, 401, 429 |
| `POST auth/refresh/` | público | 200, 401, 429 |
| `POST auth/logout/` | autenticado | 205, 400, 401 |
| `GET animales/` (filtros `especie`, `sexo`, `estado`; `search`; `ordering`) | público | 200 |
| `GET animales/{id}/` | público | 200, 404 |
| `POST animales/`, `PATCH` y `PUT animales/{id}/` | staff | 201 o 200, 400, 401, 403 |
| `DELETE animales/{id}/` | admin | 204, 403 |
| `POST solicitudes/` | autenticado | 201, 400 (duplicada), 409 (animal ya adoptado) |
| `GET solicitudes/`, `GET solicitudes/{id}/` | dueño o staff | 200, 404 |
| `POST solicitudes/{id}/cancelar/` | dueño | 200, 403, 404, 409 |
| `POST solicitudes/{id}/aprobar/` y `rechazar/` | staff | 200, 403, 404, 409 |
| `POST avistamientos/` (multipart, con foto) | autenticado | 201, 400 |
| `GET avistamientos/`, `GET avistamientos/{id}/` | dueño o staff | 200, 404 |
| `POST avistamientos/{id}/verificar/` y `descartar/` | staff | 200, 403, 404, 409 |
| `POST avistamientos/{id}/convertir/` | staff | 201, 403, 404, 409 |
| `GET usuarios/`, `GET` y `PATCH usuarios/{id}/` | admin | 200, 403 |

**Formato de las respuestas (indicador 4).** Los listados van paginados, 20 por página: `{"count", "next", "previous", "results"}`. Los errores usan el formato estándar de DRF: `{"detail": "..."}` o `{"campo": ["mensaje"]}`. No hay un formato propio.

**Principios RESTful (indicador 6).** Los recursos son sustantivos en plural y no llevan verbos. Los métodos HTTP corresponden a la operación: `GET` lee, `POST` crea, `PATCH` y `PUT` modifican, `DELETE` borra. Las acciones que no son CRUD son `POST` sobre el recurso (`/aprobar/`, `/convertir/`). La versión va en la URL. Los códigos: 201 al crear, 400 por datos inválidos, 401 sin token, 403 sin permiso, 404 si no existe, 409 si el estado actual no lo permite y 429 por exceso de intentos.

### Reglas de negocio

- Una solicitud pasa de `pendiente` a `aprobada`, `rechazada` o `cancelada`, y ya no cambia.
- Aprobar es atómico: el animal pasa a `adoptado` y las demás solicitudes pendientes de ese animal quedan `rechazada`.
- Solo se solicita un animal `adoptable`, y un usuario no puede tener dos solicitudes pendientes para el mismo animal.
- Un avistamiento `verificado` se convierte en un animal adoptable una sola vez.

### Ejemplo rápido

```bash
curl -X POST http://localhost:8000/api/v1/auth/registro/ -H "Content-Type: application/json" \
  -d '{"username":"ana","email":"ana@correo.cl","password":"Clave-Segura-123"}'
curl -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" \
  -d '{"username":"ana","password":"Clave-Segura-123"}'
curl http://localhost:8000/api/v1/solicitudes/ -H "Authorization: Bearer <access>"
```

## Seguridad (indicador 3)

Qué se aplicó y por qué:

1. **JWT con refresh rotativo y blacklist.** El access dura 15 minutos y el refresh 30 días. Cada refresh se usa una sola vez y `logout` lo invalida. Se eligió JWT en vez de `TokenAuthentication` porque este último no se puede revocar. La sesión se renueva sola mientras se usa, así que el usuario no vuelve a loguearse. No hay OTP ni sesión única (fuera de alcance).
2. **Throttling.** 5 intentos por minuto por IP en registro, login y refresh; 60 por minuto para anónimos y 120 para autenticados en el resto.
3. **Contraseñas** validadas con los validadores de Django al registrarse (largo mínimo, no comunes, no solo números).
4. **Secretos en `.env`**, que no se versiona. No hay claves en el código.
5. **Permisos cerrados por defecto** (`IsAuthenticated`). Lo público se abre explícitamente en cada vista.
6. **Sin escalada de privilegios.** El registro ignora `is_staff` e `is_superuser`. Solo un admin cambia roles, y `is_superuser` no se puede modificar por la API.
7. **Login sin pistas.** El mismo error si falla el usuario o la clave.
8. **Endpoints públicos sin autenticación.** Registro y refresh no leen el header `Authorization`, para que un token vencido en el cliente no los bloquee.
9. **Fotos.** Solo jpg, png y webp; máximo 5 MB; el contenido se verifica con Pillow y no solo la extensión; se guardan con nombre UUID.
10. **Recursos ajenos.** Un adoptante que pide una solicitud o un avistamiento de otra persona recibe 404, para no revelar que existe.
11. **Respuestas solo JSON**, sin la API navegable de DRF.

Pendiente para un despliegue real (no lo exige la pauta): HTTPS (`SECURE_SSL_REDIRECT`, HSTS, cookies seguras), servir `media/` desde un servidor de archivos y almacenamiento externo para las fotos.

## Uso de IA (indicador 7)

El diseño, el plan de implementación y gran parte del código se hicieron con apoyo de una IA (Claude). Cada decisión relevante queda registrada en [`docs/uso-ia.md`](docs/uso-ia.md): qué se preguntó, qué recomendó la IA, cómo se verificó (documentación oficial, tests, pruebas manuales) y qué se aceptó, cambió o rechazó. El plan de implementación está en `docs/superpowers/plans/2026-10-06-cumplir-pauta-eva3.md`.
