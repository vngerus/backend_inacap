# Avance Proyecto Django - Registro MVT

Este repositorio contiene el paso a paso para la creación de un motor web funcional utilizando el framework Django, aplicando el patrón MVT (Model, View, Template) y las buenas prácticas de desarrollo de la Unidad 1.

## Fase 1: Entorno Virtual y Dependencias

Para aislar el proyecto y evitar conflictos de paquetes:

```bash
python -m venv venv
source venv/Scripts/activate
pip install django pillow
pip freeze > requirements.txt
```

`pillow` es requisito de Django para `ImageField` (Fase 3) — sin él, `makemigrations` falla.

## Fase 2: Iniciar Proyecto y Aplicación

```bash
django-admin startproject avance_proyecto .
python manage.py startapp registro
```

_Configuración:_ Agregar `'registro'` a la lista `INSTALLED_APPS` en `avance_proyecto/settings.py`.

## Fase 3: El Modelo (Model)

Definición de la estructura de datos en `registro/models.py`. `Michi` se relaciona con `Dueno` (`ForeignKey`, uno-a-muchos: un dueño puede tener varios michis) y usa `ImageField` (paquete externo **Pillow**, requerido por Django para campos de imagen) para la foto:

```python
from django.db import models


class Dueno(models.Model):
    nombre = models.CharField(max_length=80)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre


class Michi(models.Model):
    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)
    dueno = models.ForeignKey(
        Dueno, on_delete=models.CASCADE, related_name='michis',
        null=True, blank=True,
    )
    foto = models.ImageField(upload_to='michis/', blank=True, null=True)

    def __str__(self):
        return self.nombre
```

`dueno`/`foto` son opcionales (`null=True, blank=True`) para no romper los datos de prueba existentes que no los traían.

## Fase 4: Migraciones

Para aplicar la estructura a la base de datos local:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Fase 5: Inserción de Datos (Django Shell)

Poblando la base de datos interactuando directamente con el modelo:

```bash
python manage.py shell
```

```python
from registro.models import Dueno, Michi
ana = Dueno.objects.create(nombre="Ana", telefono="+56911111111")
Michi.objects.create(nombre="Luna", tipo="calicó", dueno=ana)
Michi.objects.create(nombre="Kimchi", tipo="naranja", dueno=ana)
Michi.objects.create(nombre="Léa", tipo="tuxedo")
exit()
```

## Fase 6: El Admin

Registro del modelo en `registro/admin.py` para gestionarlo desde `/admin/` (CRUD completo viene incluido por Django al registrar el modelo):

```python
from django.contrib import admin
from .models import Michi


@admin.register(Michi)
class MichiAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    search_fields = ('nombre', 'tipo')

    class Media:
        css = {'all': ('registro/admin_light.css',)}
```

`registro/static/registro/admin_light.css` fuerza `color-scheme: only light` — el admin trae dark mode automático (según el SO) desde Django 3.2+, esto lo deja fijo en claro.

Crear superusuario para acceder (comando interactivo, pide username/email/password — no hay credenciales fijas en el repo):

```bash
python manage.py createsuperuser
```

## Fase 7: Las Vistas (Views)

Vistas genéricas (`ListView`/`DetailView`) para listar y ver detalle, más una vista con formulario en `registro/views.py`:

```python
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic

from .forms import MichiForm
from .models import Michi


class ListaMichisView(generic.ListView):
    template_name = 'registro/lista.html'
    context_object_name = 'michis'

    def get_queryset(self):
        return Michi.objects.all()


class DetalleMichiView(generic.DetailView):
    model = Michi
    template_name = 'registro/detalle.html'
    context_object_name = 'michi'


def agregar_michi(request):
    if request.method == 'POST':
        form = MichiForm(request.POST)
        if form.is_valid():
            michi = form.save()
            return redirect(reverse('detalle_michi', args=(michi.id,)))
    else:
        form = MichiForm()
    return render(request, 'registro/agregar.html', {
        'form': form,
        'titulo': 'Agregar michi',
        'action_url': reverse('agregar_michi'),
    })


def editar_michi(request, pk):
    michi = get_object_or_404(Michi, pk=pk)
    if request.method == 'POST':
        form = MichiForm(request.POST, instance=michi)
        if form.is_valid():
            form.save()
            return redirect(reverse('detalle_michi', args=(michi.id,)))
    else:
        form = MichiForm(instance=michi)
    return render(request, 'registro/agregar.html', {
        'form': form,
        'titulo': 'Editar michi',
        'action_url': reverse('editar_michi', args=(michi.id,)),
    })
```

## Fase 8: El Formulario (Forms)

`ModelForm` en `registro/forms.py`, reutilizado por agregar y editar:

```python
from django import forms
from .models import Michi

class MichiForm(forms.ModelForm):
    class Meta:
        model = Michi
        fields = ['nombre', 'tipo']
```

## Fase 9: Enrutamiento (URL Routing)

`registro/urls.py`, incluido desde `avance_proyecto/urls.py` con `include()`:

```python
# registro/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaMichisView.as_view(), name='lista_michis'),
    path('agregar/', views.agregar_michi, name='agregar_michi'),
    path('<int:pk>/', views.DetalleMichiView.as_view(), name='detalle_michi'),
    path('<int:pk>/editar/', views.editar_michi, name='editar_michi'),
]
```

```python
# avance_proyecto/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('michis/', include('registro.urls')),
]
```

## Fase 10: La Presentación (Templates)

Templates en `registro/templates/registro/` (`base.html`, `lista.html`, `detalle.html`, `agregar.html`) usando Tailwind vía CDN, sin CSS propio — solo utilidades, incluyendo variantes `before:`/`after:` para el detalle decorativo de "orejas" en las tarjetas.

## Fase 11: Ejecución del Servidor

```bash
python manage.py runserver
```

Rutas disponibles:

- `http://127.0.0.1:8000/michis/` — listado
- `http://127.0.0.1:8000/michis/<id>/` — detalle
- `http://127.0.0.1:8000/michis/agregar/` — agregar
- `http://127.0.0.1:8000/michis/<id>/editar/` — editar
- `http://127.0.0.1:8000/admin/` — admin de Django

## Fase 12: Correspondencia con MVC

Django implementa el patrón **MVT** (Model-View-Template), variante de MVC:

| MVC | MVT (Django) | Archivo en este proyecto |
|---|---|---|
| Model | Model | `registro/models.py` (`Michi`) |
| Controller | View | `registro/views.py` |
| View | Template | `registro/templates/registro/*.html` |

El "Controller" de MVC lo asume el propio framework (URL dispatcher + View), por eso Django llama "View" a lo que en MVC es el Controller, y "Template" a lo que en MVC es la View. Misma separación de responsabilidades: el modelo no sabe de HTTP, la vista no arma HTML a mano, el template no consulta la base de datos.

## Fase 13: Protocolos, hosting y dominios

- **Protocolo:** en desarrollo local corre sobre HTTP plano (`runserver`). En producción se serviría sobre HTTPS (TLS) detrás de un proxy (nginx/Caddy) que termina el certificado y reenvía a Django vía WSGI/ASGI (`avance_proyecto/wsgi.py`).
- **Hosting:** SQLite (archivo local `db.sqlite3`) sirve solo para desarrollo. `avance_proyecto/settings.py` ya lee `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS` desde variables de entorno (con default de desarrollo si no están seteadas), así que para producción basta con exportarlas — sin tocar código — junto con un servidor de aplicación (gunicorn/uwsgi) y una base de datos gestionada (Postgres/MySQL) en vez de SQLite.
- **Dominio:** el dominio público apuntaría (registro DNS tipo A/CNAME) a la IP del host donde corre el proxy; `ALLOWED_HOSTS` en `settings.py` debe incluir ese dominio o Django rechaza la petición.

## Fase 14: Uso de IA

Se usó IA (Claude Code) como apoyo en:

- **Generación de datos de prueba** (`registro/tests.py`, `DATOS_PRUEBA`): 5 registros variados por tipo/pelaje, validados con `full_clean()` en `test_datos_prueba_son_validos` antes de darlos por buenos — no se usaron a ciegas.
- **Modelado de relaciones**: sugerencia de agregar `Dueno` (FK desde `Michi`) para cubrir el contenido de "modelos y relaciones", verificada con `test_relacion_dueno_michis` (related_name `michis`) antes de aceptarla.
- **Cobertura de tests**: vistas de listado/detalle/agregar/editar cubiertas en `RegistroViewsTests`, verificadas corriendo `python manage.py test registro` (8/8 pasando) en vez de solo confiar en la recomendación.
- **Diseño de interfaz**: templates con Tailwind vía CDN (Fase 10).

Toda sugerencia de IA se corrió y verificó localmente antes de incorporarse (migraciones aplicadas, tests ejecutados, servidor probado en `/michis/`).

## Fase 15: CRUD completo — Delete

Se agregó la operación que faltaba (`MichiDeleteView`, `generic.DeleteView`) para completar Create/Read/Update/**Delete**:

- `registro/views.py`: `MichiDeleteView`.
- `registro/urls.py`: `<int:pk>/eliminar/`.
- `registro/templates/registro/confirmar_eliminar.html`: confirmación antes de borrar (evita delete accidental por GET).

## Fase 16: Sesiones y autenticación

Rutas de **lectura** (`lista_michis`, `detalle_michi`) siguen públicas. Rutas de **escritura** (`agregar_michi`, `editar_michi`, `eliminar_michi`) ahora requieren sesión iniciada:

```bash
python manage.py createsuperuser  # o cualquier usuario vía shell/admin
```

- `django.contrib.auth` ya venía en `INSTALLED_APPS`/`MIDDLEWARE` (default de Django) — se usó tal cual, sin dependencias nuevas.
- `@login_required` en las vistas function-based (`agregar_michi`, `editar_michi`); `LoginRequiredMixin` en `MichiDeleteView`.
- `LOGIN_URL`/`LOGIN_REDIRECT_URL`/`LOGOUT_REDIRECT_URL` en `settings.py` — redirige a `/accounts/login/` y de vuelta al listado.
- Sesión persiste vía `django.contrib.sessions` (cookie de sesión, backend default de Django — sin configuración extra).
- `python manage.py test registro` — 15/15 tests pasando, incluye `AutenticacionTests` (anónimo redirigido a login, usuario autenticado puede operar).

## Fase 17: Base de datos — MySQL vía Docker

Cambio de motor pedido por el curso (MySQL/XAMPP). En vez de instalar XAMPP, se usa un contenedor Docker equivalente (mismo resultado: un MySQL escuchando en `localhost`):

```bash
docker run -d --name inacap_mysql -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=inacap -e MYSQL_DATABASE=michis_eva02 \
  mysql:8.0
```

- `avance_proyecto/settings.py`: `DATABASES['default']` apunta a MySQL, credenciales vía variables de entorno (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) con defaults que calzan con el contenedor de arriba.
- Driver: `PyMySQL` (puro Python, no requiere compilador C en Windows como sí pide `mysqlclient`). Shim `pymysql.install_as_MySQLdb()` en `avance_proyecto/__init__.py` — Django solo sabe hablar con la API de `MySQLdb`.
- Puerto `3307` (no `3306`) para no chocar con otro contenedor MySQL ya en uso en esta máquina para otro proyecto.
- Migrado y verificado: `python manage.py migrate` + `python manage.py test registro` (15/15) corriendo contra el MySQL real del contenedor, no SQLite.

La rama `Desarrollo_Django-eva02-postgres` parte de este mismo punto y cambia el motor a PostgreSQL:

```bash
git checkout Desarrollo_Django-eva02-postgres
```
