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

class Gato(models.Model):
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
from registro.models import Gato
Gato.objects.create(nombre="Luna", tipo="calicó")
Gato.objects.create(nombre="Kimchi", tipo="naranja")
Gato.objects.create(nombre="Léa", tipo="tuxedo")
exit()
```

## Fase 6: La Vista (View)

Lógica para procesar la solicitud en `registro/views.py`:

```python
from django.shortcuts import render
from .models import Gato

def lista_gatos(request):
    gatos = Gato.objects.all()
    return render(request, 'registro/lista.html', {'gatos': gatos})
```

## Fase 7: Enrutamiento (URL Routing)

Conexión de la dirección web con la vista en `avance_proyecto/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from registro.views import lista_gatos

urlpatterns = [
    path('admin/', admin.site.urls),
    path('mis-gatos/', lista_gatos, name='lista_gatos'),
]
```

## Fase 8: La Presentación (Template)

Creación de la interfaz en `registro/templates/registro/lista.html`:

```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <title>Michis</title>
  </head>
  <body>
    <h1>Registro MVT: Mis Gatos</h1>
    <div>
      {% for gato in gatos %}
      <div><strong>{{ gato.nombre }}</strong> - Tipo: {{ gato.tipo }}</div>
      {% empty %}
      <p>No hay gatitos registrados todavía.</p>
      {% endfor %}
    </div>
  </body>
</html>
```

## Fase 9: Ejecución del Servidor

```bash
python manage.py runserver
```

El navegador web la ruta `http://127.0.0.1:8000/mis-gatos/` para visualizar los datos renderizados y obtener un código de estado HTTP 200 exitoso.
