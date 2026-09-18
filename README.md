# Backend INACAP

Repositorio general para los proyectos del ramo de backend (TI3V41 — Desarrollo de aplicaciones del lado del servidor).

Uso educacional — ver [LICENSE](LICENSE) (MIT + nota académica).

## Estructura

```text
proyectos/
└── 2026/
    └── unidad-01-tecnologias-servidor/
        ├── Desarrollo_Django-eva01/   # Evaluación 1 (Unidad 1) — cerrada
        └── Desarrollo_Django-eva02/   # Evaluación 2 (Unidad 2) — copia de eva01, CRUD+admin+sesiones
```

Cada entrega Django es independiente: propio `manage.py`, `settings.py`, migraciones. `Desarrollo_Django-eva02` nace como copia de `Desarrollo_Django-eva01` en el punto donde esa evaluación quedó cerrada — `Desarrollo_Django-eva01` ya no se modifica.

### Ramas

| Rama | Contenido | Motor de BD |
|---|---|---|
| `main` | `Desarrollo_Django-eva01` (cerrada) + `Desarrollo_Django-eva02` | MySQL (Docker) |
| `Desarrollo_Django-eva02-postgres` | Mismo `Desarrollo_Django-eva02`, bifurcado tras cerrar CRUD+auth | PostgreSQL (Docker) |

El profesor pidió usar MySQL (vía XAMPP) en una variante y PostgreSQL en otra. Se usó Docker en vez de XAMPP para tener el mismo resultado (un MySQL escuchando en `localhost`) sin instalar nada a nivel de sistema — ver detalle en el README de `Desarrollo_Django-eva02` (Fase 17).

## Evaluación 1 — cumplimiento (`Desarrollo_Django-eva01`)

12 indicadores de la escala de apreciación de Unidad 1 (variables/operadores, paquetes externos, app Django funcional, MVC/MVT, config de entorno, Models con relaciones, vistas/templates, tecnologías de servidor, uso de IA + datos de prueba, protocolos/hosting/dominio) — todos documentados fase a fase en `Desarrollo_Django-eva01/README.md`. Carpeta cerrada, no recibe más cambios.

## Evaluación 2 — cumplimiento (`Desarrollo_Django-eva02`)

Escala de apreciación de Unidad 2 (Django Admin + CRUD), 6 indicadores — todos en nivel Logrado o superior:

| Indicador | Cómo se cumple |
|---|---|
| 2.1.1 Configuración de BD | `avance_proyecto/settings.py` — motor vía Docker (MySQL en `main`, Postgres en `Desarrollo_Django-eva02-postgres`), credenciales por variable de entorno, sin hardcodear |
| 2.1.2 Uso de Django Admin | `registro/admin.py` — `DuenoAdmin`/`MichiAdmin` con `list_display`, `search_fields`, `list_filter`, CSS custom |
| 2.1.3 Operaciones CRUD | `registro/views.py` — Create/Read/Update/**Delete** completos (`MichiDeleteView` agregado) |
| 2.1.4 Backend + seguridad | CSRF (default Django) + rutas de escritura protegidas con `@login_required`/`LoginRequiredMixin` |
| Gestión de sesiones y autenticación | `django.contrib.auth` — login/logout, `LOGIN_URL`/`LOGIN_REDIRECT_URL`, rutas de lectura públicas y de escritura protegidas |
| Uso de IA | `Desarrollo_Django-eva02/README.md` Fase 14 — qué se pidió a la IA y cómo se verificó cada sugerencia (tests, `full_clean()`, corridas locales) |

Detalle fase a fase (incluye Fase 15 Delete, Fase 16 sesiones, Fase 17 base de datos) en `Desarrollo_Django-eva02/README.md`.

## Entorno virtual

Compartido a nivel de repo, no se versiona:

```bash
python -m venv venv
source venv/Scripts/activate       # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Levantar una entrega

### Evaluación 1 (SQLite, sin dependencias externas)

```bash
cd proyectos/2026/unidad-01-tecnologias-servidor/Desarrollo_Django-eva01
python manage.py runserver
```

### Evaluación 2 — MySQL (rama `main`)

```bash
docker run -d --name inacap_mysql -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=inacap -e MYSQL_DATABASE=michis_eva02 \
  mysql:8.0

cd proyectos/2026/unidad-01-tecnologias-servidor/Desarrollo_Django-eva02
python manage.py migrate
python manage.py test registro
python manage.py runserver
```

### Evaluación 2 — PostgreSQL (rama `Desarrollo_Django-eva02-postgres`)

```bash
git checkout Desarrollo_Django-eva02-postgres

docker run -d --name inacap_postgres -p 5433:5432 \
  -e POSTGRES_PASSWORD=inacap -e POSTGRES_DB=michis_eva02 \
  postgres:16

cd proyectos/2026/unidad-01-tecnologias-servidor/Desarrollo_Django-eva02
python manage.py migrate
python manage.py test registro
python manage.py runserver
```

En ambos casos hay que crear un usuario antes de poder usar `agregar`/`editar`/`eliminar` (protegidos con login):

```bash
python manage.py createsuperuser
```
