# API de Adopción de Animales

API REST hecha con Django REST Framework para un refugio de animales. Proyecto del ramo de desarrollo de aplicaciones del lado del servidor (INACAP, TI3V41).

## Qué hace

- **Publica animales** adoptables, con foto, y permite filtrarlos por especie, sexo y estado, además de buscar y ordenar.
- **Gestiona solicitudes de adopción.** Cualquier persona registrada puede pedir un animal; el personal del refugio aprueba o rechaza. Una solicitud pasa de `pendiente` a `aprobada`, `rechazada` o `cancelada`, y ya no cambia.
- **Recibe avistamientos.** Cualquier usuario puede reportar un animal visto en la calle, con foto y ubicación. El personal lo verifica y, si corresponde, lo convierte en un animal adoptable.
- **Controla quién puede hacer qué** con tres roles: adoptante, staff y admin.

Todas las respuestas son JSON. La autenticación es con tokens JWT, y la documentación interactiva está en Swagger.

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

La app no arranca sin `DJANGO_SECRET_KEY`. Es a propósito: así no existe una clave por defecto que alguien pueda olvidar cambiar.

| Variable de `.env` | Para qué | Ejemplo |
|---|---|---|
| `DJANGO_SECRET_KEY` | firma de tokens (obligatoria) | clave aleatoria larga |
| `DJANGO_DEBUG` | `1` en desarrollo (también sirve las fotos), `0` en producción | `1` |
| `DJANGO_ALLOWED_HOSTS` | hosts permitidos, separados por coma | `localhost,127.0.0.1` |

Con el servidor corriendo:

- Swagger, para leer la documentación y probar los endpoints: http://localhost:8000/api/docs/
- Schema OpenAPI: http://localhost:8000/api/schema/
- `requests.http`: colección de requests de ejemplo (extensión REST Client de VS Code).

### Pruebas automáticas

```bash
python manage.py test
```

Hay 68 tests. Cubren el registro y el login, la rotación de tokens, los permisos de cada rol, el ciclo de las solicitudes, la validación de fotos, la conversión de avistamientos y que Swagger documente todos los recursos.

## Roles

Los roles son jerárquicos: cada uno puede lo del anterior.

| Rol | Cómo se obtiene | Puede |
|---|---|---|
| Adoptante | se registra en la API | ver animales, solicitar adopción, ver y cancelar sus solicitudes, reportar avistamientos y ver los suyos |
| Staff | un admin lo promueve | crear y editar animales, aprobar y rechazar solicitudes, verificar, descartar y convertir avistamientos, y ver todo lo de los demás |
| Admin | `createsuperuser` | borrar animales y gestionar usuarios: promover a staff y desactivar cuentas |

## Endpoints

La referencia completa (rutas, parámetros, cuerpos y respuestas) está en Swagger: http://localhost:8000/api/docs/. Se genera desde el código, así que siempre está al día, y desde ahí se puede probar cada endpoint con el botón **Authorize**.

Todos cuelgan de `/api/v1/` y siguen el mismo patrón:

- **Recursos** en plural: `auth/`, `animales/`, `solicitudes/`, `avistamientos/` y `usuarios/`.
- **Acciones** que no son CRUD como `POST` sobre el recurso: `solicitudes/{id}/aprobar/`, `avistamientos/{id}/convertir/`.
- **Lectura pública** solo en `animales/`. El resto exige token.

**Paginación y errores.** Los listados van paginados, 20 por página: `{"count", "next", "previous", "results"}`. Los errores usan el formato estándar de DRF: `{"detail": "..."}` para errores generales y `{"campo": ["mensaje"]}` para datos inválidos.

**Códigos de respuesta.** 201 al crear, 400 por datos inválidos, 401 sin token, 403 sin permiso, 404 si no existe, 409 si el estado actual no permite la acción (por ejemplo, aprobar una solicitud que ya se resolvió) y 429 por demasiados intentos.

### Reglas de negocio

- Aprobar una solicitud es una operación atómica: el animal pasa a `adoptado` y las demás solicitudes pendientes de ese animal quedan `rechazada`.
- Solo se puede solicitar un animal `adoptable`, y un usuario no puede tener dos solicitudes pendientes para el mismo animal.
- Un avistamiento solo se convierte en animal si está `verificado`, y solo una vez.

### Ejemplo rápido

```bash
curl -X POST http://localhost:8000/api/v1/auth/registro/ -H "Content-Type: application/json" \
  -d '{"username":"ana","email":"ana@correo.cl","password":"Clave-Segura-123"}'
curl -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" \
  -d '{"username":"ana","password":"Clave-Segura-123"}'
curl http://localhost:8000/api/v1/solicitudes/ -H "Authorization: Bearer <access>"
```

## Cómo se protege la API

1. **JWT con refresh rotativo.** El token de acceso dura 15 minutos y el de renovación 30 días. Cada token de renovación se usa una sola vez, y `logout` lo invalida. Mientras la persona use la app, la sesión se renueva sola y no tiene que volver a loguearse. Se eligió JWT en vez del token simple de DRF porque ese no se puede revocar.
2. **Límite de intentos.** 5 por minuto por IP en registro, login y refresh; 60 por minuto para anónimos y 120 para usuarios autenticados en el resto.
3. **Contraseñas** validadas con los validadores de Django al registrarse: largo mínimo, no comunes y no solo números.
4. **Secretos en `.env`**, que no se sube al repositorio. No hay claves en el código.
5. **Permisos cerrados por defecto.** Todo exige autenticación, y lo público se abre explícitamente en cada vista.
6. **Nadie se asciende solo.** El registro ignora `is_staff` e `is_superuser`; solo un admin cambia roles, y `is_superuser` no se puede modificar por la API.
7. **Login sin pistas.** Si falla, el error es el mismo se equivoque el usuario o la clave.
8. **Registro y refresh no leen el header `Authorization`.** Así un token vencido que el cliente aún guarda no bloquea esas dos operaciones.
9. **Fotos controladas.** Solo jpg, png y webp, hasta 5 MB. Se verifica el contenido real de la imagen con Pillow y no solo la extensión, y se guardan con nombre aleatorio.
10. **Recursos ajenos.** Si un adoptante pide una solicitud o un avistamiento de otra persona, recibe 404 y no 403, para no revelar que existe.
11. **Solo JSON.** Se desactivó la API navegable de DRF.

Falta para un despliegue real: HTTPS (`SECURE_SSL_REDIRECT`, HSTS y cookies seguras), servir `media/` desde un servidor de archivos y guardar las fotos en un almacenamiento externo.

## Desarrollo con IA

El plan de implementación se hizo con IA (Claude Code) usando el plugin Superpowers: se diseñó la API, se escribió un plan por tareas con tests primero y se ejecutó tarea por tarea. El plan queda en `docs/superpowers/plans/`. Las decisiones de diseño y las pruebas en Swagger las revisé y ajusté yo.
