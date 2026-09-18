# Contexto del proyecto

Proyecto Django académico (INACAP, TI3V41 Unidad 2 — "Aplicación web con Django Admin y con CRUD"). Copia de `../Desarrollo_Django-eva01/` (entrega eval1, ya cerrada — no tocar desde acá) sobre la que se agrega Delete al CRUD, login/sesiones y (pendiente) migración a Postgres. Evaluado con escala de apreciación propia de esta unidad, 6 indicadores, 4 niveles (Inicial/En desarrollo/Logrado/Destacado). Plan de implementación: `docs/superpowers/plans/2026-09-17-cumplir-pauta-eval2.md`.

## Skills instaladas — cuándo usar cada una

Ver `../../../../skills-lock.json` (compartidas a nivel de repo, no por unidad). Todas orientadas a frontend/diseño — no hay skill Django específica instalada.

| Skill | Usar cuando |
|---|---|
| `accessibility` | Templates con formularios o interacción — cumple indicador 8 (vistas/templates de calidad) |
| `frontend-design` / `huashu-design` | Diseñar interfaces de templates — cubre "IA como apoyo a diseño de interfaces" (contenido mínimo obligatorio) |
| `seo` | Solo si el proyecto expone páginas públicas — normalmente no aplica a este ejercicio |

## Buenas prácticas transversales (mapeadas a la rúbrica)

- **`ponytail`** (global): antes de escribir un modelo, vista o serializer nuevo, pasar por la escalera de simplicidad — Django ya resuelve la mayoría (ORM, class-based views, admin) sin código custom. Mapea a indicador 2 ("implementa soluciones eficientes, ordenadas") y evita sobre-ingeniería que baje nota en indicador 4.
- **CodeGraph** (ya indexado en este proyecto — 59 archivos, 530 nodes): usar `codegraph_search`/`codegraph_context`/`codegraph_impact` antes de tocar models compartidos entre apps — evita romper relaciones (indicador 7, "diseña modelos considerando relaciones y buenas prácticas") y ayuda a explicar/justificar decisiones (nivel Destacado en varios indicadores pide justificar elección).
- **`superpowers:systematic-debugging`** (global): al depurar errores de configuración Django (indicador 6) — diagnosticar causa raíz antes de parchear.
- **`superpowers:test-driven-development`** (global): para indicador 11 (datos de prueba) — generar fixtures/datos vía IA y verificarlos con test antes de darlos por buenos, no solo pegarlos.

## Buenas prácticas Django (contenidos mínimos del curso)

- MVT de Django (equivalente al MVC del temario): mantener lógica de negocio fuera de templates y vistas delgadas — vistas solo orquestan, models tienen la lógica de datos.
- `settings.py`: no hardcodear secrets; usar variables de entorno para deploy (protocolos/hosting/dominios — indicador 12).
- Migraciones: una por cambio lógico de modelo, nombre descriptivo — facilita justificar decisiones de modelado.
- Documentar pasos de configuración del entorno en el README del proyecto (indicador 6, nivel Destacado pide "documentando pasos").
