# Cumplir Pauta Escala de Apreciación (Eval 2) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar los dos gaps de la "Escala de Apreciación Django" (criterios 2.1.3 CRUD y "Gestión de Sesiones y Autenticación") en el proyecto `registro` para que ambos indicadores lleguen a nivel "Logrado" (3 ptos) como mínimo.

**Architecture:** Todo se resuelve con piezas nativas de Django — `generic.DeleteView` para el Delete que falta, y `django.contrib.auth` (ya en `INSTALLED_APPS`/`MIDDLEWARE`) para login/logout y protección de rutas de escritura con `login_required`/`LoginRequiredMixin`. No se agregan dependencias nuevas.

**Tech Stack:** Django 5.2 (ya instalado), `django.contrib.auth` (stdlib de Django, ya habilitado), sqlite3, pytest no — usa `python manage.py test` (Django TestCase, ya en uso en `registro/tests.py`).

**Spec:** Pauta del usuario en `C:\Users\Angel Smith\Downloads\Escala_de_Apreciacion_Django_eva2.pdf` (criterios 2.1.1–2.1.4 + "Gestión de Sesiones y Autenticación"). Gaps identificados en conversación: (1) CRUD sin Delete, (2) sin login/sesiones protegiendo rutas de escritura. Criterio 6 (Uso de IA) ya está cubierto por `README.md` Fase 14 — no requiere cambios.

## Global Constraints

- Proyecto vive en `proyectos/2026/unidad-01-tecnologias-servidor/Desarrollo_Django-eva02/` — todas las rutas de este plan son relativas a esa carpeta. Es copia de `Desarrollo_Django-eva01/` (entrega ya cerrada de eval1), no se toca esa carpeta desde acá.
- No agregar dependencias nuevas (`pip install` nada) — todo lo necesario ya está en Django stdlib/contrib.
- Vistas de **lectura** (`lista_michis`, `detalle_michi`) siguen públicas — solo se protegen **escritura** (`agregar_michi`, `editar_michi`, `eliminar_michi`), que es lo que la pauta llama "rutas protegidas".
- Mantener el estilo Tailwind-CDN existente en templates (ver `registro/templates/registro/base.html`), sin CSS propio nuevo.
- Cada task termina con `python manage.py test registro` en verde antes del commit.

---

### Task 1: Completar CRUD — vista Delete

**Files:**
- Modify: `registro/views.py`
- Modify: `registro/urls.py`
- Create: `registro/templates/registro/confirmar_eliminar.html`
- Modify: `registro/templates/registro/detalle.html`
- Modify: `registro/tests.py`

**Interfaces:**
- Produces: URL name `eliminar_michi` (pattern `<int:pk>/eliminar/`), vista `MichiDeleteView` (class-based, `generic.DeleteView`).

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `RegistroViewsTests` en `registro/tests.py`:

```python
    def test_eliminar_michi_post(self):
        response = self.client.post(reverse('eliminar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Michi.objects.filter(id=self.michi.id).exists())

    def test_eliminar_michi_get_muestra_confirmacion(self):
        response = self.client.get(reverse('eliminar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.michi.nombre)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test registro -v 2`
Expected: `FAIL` — `NoReverseMatch: Reverse for 'eliminar_michi' not found`

- [ ] **Step 3: Agregar la vista `MichiDeleteView`**

En `registro/views.py`, agregar el import de `reverse_lazy` y la clase al final del archivo:

```python
from django.urls import reverse, reverse_lazy
```

(reemplaza la línea `from django.urls import reverse` existente)

```python
class MichiDeleteView(generic.DeleteView):
    model = Michi
    template_name = 'registro/confirmar_eliminar.html'
    context_object_name = 'michi'
    success_url = reverse_lazy('lista_michis')
```

- [ ] **Step 4: Agregar la URL**

En `registro/urls.py`, agregar antes del cierre de la lista:

```python
    path('<int:pk>/eliminar/', views.MichiDeleteView.as_view(), name='eliminar_michi'),
```

(el archivo completo queda con 5 rutas: lista, agregar, detalle, editar, eliminar)

- [ ] **Step 5: Crear el template de confirmación**

Crear `registro/templates/registro/confirmar_eliminar.html`:

```html
{% extends 'registro/base.html' %}

{% block title %}Eliminar {{ michi.nombre }} · Michis{% endblock %}

{% block content %}
    <div class="max-w-sm rounded-2xl bg-white p-8 shadow-sm border border-ink/5">
        <p class="font-display text-xl font-800 mb-2">¿Eliminar a {{ michi.nombre }}?</p>
        <p class="text-sm text-muted mb-6">Esta acción no se puede deshacer.</p>

        <form method="post" class="flex gap-3">
            {% csrf_token %}
            <button type="submit"
                    class="font-display font-700 text-sm bg-marmalade text-white px-4 py-2 rounded-full hover:bg-orange-500 transition-colors">
                Sí, eliminar
            </button>
            <a href="{% url 'detalle_michi' michi.id %}"
               class="font-display font-700 text-sm px-4 py-2 rounded-full text-ink hover:bg-ink/5 transition-colors">
                Cancelar
            </a>
        </form>
    </div>
{% endblock %}
```

- [ ] **Step 6: Enlazar el botón de eliminar desde el detalle**

En `registro/templates/registro/detalle.html`, agregar después del link de editar (después del `</a>` que cierra el link "Editar", línea 17):

```html
        <a href="{% url 'eliminar_michi' michi.id %}"
           aria-label="Eliminar {{ michi.nombre }}"
           title="Eliminar"
           class="absolute top-4 right-14 w-8 h-8 flex items-center justify-center rounded-full text-muted hover:text-red-500 hover:bg-red-50 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4">
                <path d="M3 6h18"></path>
                <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path>
            </svg>
        </a>
```

- [ ] **Step 7: Correr los tests y verificar que pasan**

Run: `python manage.py test registro -v 2`
Expected: `OK` (10 tests)

- [ ] **Step 8: Commit**

```bash
git add registro/views.py registro/urls.py registro/templates/registro/confirmar_eliminar.html registro/templates/registro/detalle.html registro/tests.py
git commit -m "feat: agregar Delete al CRUD de Michi"
```

---

### Task 2: Login/logout y protección de rutas de escritura

**Files:**
- Modify: `avance_proyecto/settings.py`
- Modify: `avance_proyecto/urls.py`
- Modify: `registro/views.py`
- Create: `registro/templates/registro/login.html`
- Modify: `registro/templates/registro/base.html`
- Modify: `registro/tests.py`

**Interfaces:**
- Consumes: `MichiDeleteView` de Task 1 (se le agrega `LoginRequiredMixin`).
- Produces: URL names `login`, `logout` (via `django.contrib.auth.urls` / `auth_views`); `settings.LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `registro/tests.py`, nueva clase:

```python
from django.contrib.auth.models import User


class AutenticacionTests(TestCase):
    def setUp(self):
        self.michi = Michi.objects.create(nombre="Luna", tipo="calico")
        self.user = User.objects.create_user(username='ana', password='clave-segura-123')

    def test_anonimo_no_puede_agregar(self):
        response = self.client.get(reverse('agregar_michi'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_anonimo_no_puede_editar(self):
        response = self.client.get(reverse('editar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_anonimo_no_puede_eliminar(self):
        response = self.client.post(reverse('eliminar_michi', args=(self.michi.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_usuario_autenticado_puede_agregar(self):
        self.client.login(username='ana', password='clave-segura-123')
        response = self.client.get(reverse('agregar_michi'))
        self.assertEqual(response.status_code, 200)

    def test_login_logout_flow(self):
        response = self.client.post(reverse('login'), {
            'username': 'ana', 'password': 'clave-segura-123',
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test registro -v 2`
Expected: `FAIL` — `NoReverseMatch: Reverse for 'login' not found`

- [ ] **Step 3: Configurar settings de auth**

En `avance_proyecto/settings.py`, agregar al final del archivo:

```python
# Autenticación / sesiones
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'lista_michis'
LOGOUT_REDIRECT_URL = 'lista_michis'
```

- [ ] **Step 4: Agregar las URLs de auth**

En `avance_proyecto/urls.py`, agregar el import y la ruta:

```python
from django.contrib.auth import views as auth_views
```

(junto a los otros imports de `django.contrib`)

```python
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registro/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
```

(agregar estas dos líneas a `urlpatterns`, antes de `path('michis/', include('registro.urls'))`)

- [ ] **Step 5: Proteger las vistas de escritura**

En `registro/views.py`, agregar imports:

```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
```

Decorar `agregar_michi` y `editar_michi` (agregar `@login_required` justo arriba de cada `def`):

```python
@login_required
def agregar_michi(request):
    ...

@login_required
def editar_michi(request, pk):
    ...
```

Hacer que `MichiDeleteView` (de Task 1) herede también de `LoginRequiredMixin`:

```python
class MichiDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Michi
    template_name = 'registro/confirmar_eliminar.html'
    context_object_name = 'michi'
    success_url = reverse_lazy('lista_michis')
```

- [ ] **Step 6: Crear el template de login**

Crear `registro/templates/registro/login.html`:

```html
{% extends 'registro/base.html' %}

{% block title %}Iniciar sesión · Michis{% endblock %}

{% block content %}
    <div class="max-w-sm rounded-2xl bg-white p-8 shadow-sm border border-ink/5">
        <p class="font-display text-xl font-800 mb-6">Iniciar sesión</p>

        {% if form.errors %}
            <p class="text-sm text-red-500 mb-4">Usuario o contraseña incorrectos.</p>
        {% endif %}

        <form method="post" class="space-y-4">
            {% csrf_token %}
            <div>
                <label class="block text-sm font-medium mb-1" for="{{ form.username.id_for_label }}">Usuario</label>
                {{ form.username }}
            </div>
            <div>
                <label class="block text-sm font-medium mb-1" for="{{ form.password.id_for_label }}">Contraseña</label>
                {{ form.password }}
            </div>
            <button type="submit"
                    class="font-display font-700 text-sm bg-marmalade text-white px-4 py-2 rounded-full hover:bg-orange-500 transition-colors">
                Entrar
            </button>
        </form>
    </div>
{% endblock %}
```

`{{ form.username }}`/`{{ form.password }}` renderizan `<input>` sin clases Tailwind (Django `AuthenticationForm` no acepta `widgets` custom sin subclasear el form) — visualmente simple pero funcional; no bloquea ningún criterio de la pauta.

- [ ] **Step 7: Agregar login/logout a la navegación**

En `registro/templates/registro/base.html`, dentro del `<div class="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between">` (línea 32), después del link "+ Agregar michi" (línea 38, antes del `</div>` de cierre en línea 39):

```html
            {% if user.is_authenticated %}
                <form method="post" action="{% url 'logout' %}" class="inline">
                    {% csrf_token %}
                    <button type="submit" class="text-sm text-muted hover:text-ink">Salir ({{ user.username }})</button>
                </form>
            {% else %}
                <a href="{% url 'login' %}" class="text-sm text-muted hover:text-ink">Entrar</a>
            {% endif %}
```

- [ ] **Step 8: Correr los tests y verificar que pasan**

Run: `python manage.py test registro -v 2`
Expected: `OK` (15 tests)

- [ ] **Step 9: Commit**

```bash
git add avance_proyecto/settings.py avance_proyecto/urls.py registro/views.py registro/templates/registro/login.html registro/templates/registro/base.html registro/tests.py
git commit -m "feat: agregar login/logout y proteger rutas de escritura"
```

---

### Task 3: Documentar en README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: nada de código — solo documenta lo hecho en Task 1 y 2.

- [ ] **Step 1: Agregar Fase 15 y 16 al README**

Al final de `README.md` (después de la Fase 14 "Uso de IA", línea 255), agregar:

```markdown

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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: documentar Delete y autenticación en README"
```

---

## Self-Review Checklist (ya aplicado al escribir este plan)

- **Cobertura:** Task 1 cierra criterio 2.1.3 (CRUD completo). Task 2 cierra "Gestión de Sesiones y Autenticación" y refuerza 2.1.4 (backend con seguridad). Criterio 6 (IA) ya cumplido en README existente — sin task nuevo.
- **Sin placeholders:** cada step tiene código completo, no hay "TODO" ni "similar a".
- **Consistencia de tipos/nombres:** `MichiDeleteView` se define en Task 1 y se modifica (no se re-declara) en Task 2; `eliminar_michi` como URL name se usa igual en template y tests en ambos tasks.
