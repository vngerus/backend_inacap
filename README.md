# Backend INACAP

Repositorio general para los proyectos del ramo de backend.

## Estructura

Los proyectos se organizan por año, unidad y fecha de seguimiento:

```text
proyectos/
└── 2026/
    └── unidad-01-tecnologias-servidor/
        └── Desarrollo_Django-eva01/
```

Cada entrega Django es independiente y tiene su propio `manage.py`, configuración,
aplicaciones, migraciones y base de datos local.

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

## Ejecutar la entrega actual

```bash
cd proyectos/2026/unidad-01-tecnologias-servidor/Desarrollo_Django-eva01
python manage.py runserver
```
