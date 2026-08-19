# Avance Proyecto Django - Registro MVT

Este repositorio contiene el paso a paso para la creación de un motor web funcional utilizando el framework Django, aplicando el patrón MVT (Model, View, Template) y las buenas prácticas de desarrollo de la Unidad 1.

## Fase 1: Entorno Virtual y Dependencias

Para aislar el proyecto y evitar conflictos de paquetes:

```bash
python -m venv venv
source venv/Scripts/activate
pip install django
pip freeze > requirements.txt
```

## Fase 2: Iniciar Proyecto y Aplicación

```bash
django-admin startproject avance_proyecto .
python manage.py startapp registro
```

_Configuración:_ Agregar `'registro'` a la lista `INSTALLED_APPS` en `avance_proyecto/settings.py`.

## Fase 3: El Modelo (Model)

Definición de la estructura de datos en `registro/models.py`:

```python
from django.db import models

class Michi(models.Model):
    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
```

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
from registro.models import Michi
Michi.objects.create(nombre="Luna", tipo="calicó")
Michi.objects.create(nombre="Kimchi", tipo="naranja")
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
