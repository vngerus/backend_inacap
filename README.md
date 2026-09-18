# Backend INACAP

Repositorio general para los proyectos del ramo de backend.

## Estructura

Los proyectos se organizan por año, unidad, y carpeta por evaluación:

```text
proyectos/
└── 2026/
    └── unidad-01-tecnologias-servidor/
        ├── Desarrollo_Django-eva01/   # Evaluación 1 (Unidad 1) — cerrada
        └── Desarrollo_Django-eva02/   # Evaluación 2 (Unidad 2) — en curso, parte de eva01
```

Cada entrega Django es independiente y tiene su propio `manage.py`, configuración,
aplicaciones, migraciones y base de datos local. `Desarrollo_Django-eva02` nace como
copia de `Desarrollo_Django-eva01` en el punto donde esa evaluación quedó cerrada —
`Desarrollo_Django-eva01` ya no se modifica.

## Entorno virtual

El entorno virtual se mantiene en la raíz del repositorio y no se versiona:

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

En Windows también se puede activar con:

```powershell
venv\Scripts\Activate.ps1
```

## Ejecutar una entrega

```bash
cd proyectos/2026/unidad-01-tecnologias-servidor/Desarrollo_Django-eva02  # o eva01
python manage.py runserver
```
