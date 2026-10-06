# Contexto del proyecto

Proyecto Django académico (INACAP, TI3V41 Unidad 3 — "Aplicación API RESTful", 35%, desarrollo individual). API REST con Django REST Framework para adopción de animales: `Animal`, `SolicitudAdopcion` y `Avistamiento`, con JWT y roles jerárquicos (adoptante < staff < admin). Proyecto independiente de `../../unidad-01-tecnologias-servidor/Desarrollo_Django-eva01` y `eva02` (ya evaluadas, no tocar). Se trabaja en `main`. Evaluado con escala de apreciación de 7 indicadores y 4 niveles (Inicial/En desarrollo/Logrado/Destacado); la meta es Destacado en todos. Plan de implementación: `docs/superpowers/plans/2026-10-06-cumplir-pauta-eva3.md`. Pauta: `C:\Users\Angel Smith\Downloads\Escala_Apreciacion_Unidad_3_API_RESTful.pdf`.

## Indicadores de la pauta → dónde se cumplen

| # | Indicador (peso) | Dónde vive | Evidencia |
|---|---|---|---|
| 1 | Configura DRF según documentación oficial (15%) | `config/settings.py` (`REST_FRAMEWORK`, `SIMPLE_JWT`, `SPECTACULAR_SETTINGS`), estructura de 4 apps | `config/tests.py`, README secciones 1-3 |
| 2 | Implementa autenticación (20%) | `cuentas/` (registro, login, refresh, logout, roles) | `cuentas/tests.py` |
| 3 | Recomendaciones de seguridad en la autenticación (15%) | throttling, validadores de contraseña, blacklist, `.env`, sin escalada, fotos validadas | README sección 7, `docs/uso-ia.md` |
| 4 | Respuestas JSON (15%) | renderer solo JSON, paginación `{count,next,previous,results}`, errores estándar DRF | tests por app |
| 5 | Endpoints según requerimientos (15%) | `animales/`, `adopciones/`, `avistamientos/`, `cuentas/` | README sección 6, Swagger `/api/docs/` |
| 6 | Características RESTful (10%) | `/api/v1/`, recursos en plural, métodos HTTP, 201/400/401/403/404/409/429 | tests de códigos de respuesta |
| 7 | Uso de IA crítico y responsable (10%) | `docs/uso-ia.md` | una entrada por decisión: qué se pidió, qué recomendó la IA, cómo se verificó, qué se cambió |

Productos esperados de la pauta: proyecto funcional, DRF configurado, recurso expuesto, endpoints, JSON, operaciones HTTP, autenticación, seguridad, **pruebas de endpoints**, **evidencia de uso de IA** y **README con instalación, configuración y ejecución**.

## Skills — cuándo usar cada una

Ver `../../../../skills-lock.json` (compartidas a nivel de repo). Orientadas a frontend/diseño; no hay skill de DRF instalada, así que la referencia es la documentación oficial (DRF, simplejwt, drf-spectacular).

| Skill | Usar cuando |
|---|---|
| `superpowers:test-driven-development` | siempre: test que falla primero, después el código (indicador 6, y evidencia de pruebas) |
| `superpowers:systematic-debugging` | al depurar errores de configuración o de permisos: causa raíz antes de parchear |
| `ponytail` | antes de escribir modelo, serializer o vista nueva: DRF ya trae la mayoría (viewsets, router, filtros, paginación) |
| `security-review` | antes de cerrar la task de autenticación y la de fotos (indicador 3) |

## Convenciones de este proyecto

- **Lógica de negocio en el modelo, vistas delgadas**: transiciones de estado (`aprobar`, `rechazar`, `cancelar`, `verificar`, `convertir`) son métodos del modelo; las vistas solo llaman y responden.
- **Códigos de respuesta**: 409 (`config.exceptions.Conflicto`) para conflictos de estado; 400 para datos inválidos; 404 (no 403) cuando un adoptante pide un recurso ajeno.
- **Permisos**: `cuentas.permissions.IsStaff` (staff o superusuario) e `IsAdmin` (superusuario); por defecto todo es `IsAuthenticated` y lo público se abre a mano.
- **Roles por `is_staff`/`is_superuser`** de Django. No hay modelo de roles propio. El registro nunca crea staff.
- **Tests**: `python manage.py test`, extienden `config.pruebas.BaseAPITest` (limpia el cache del throttling y crea ana, beto, sofia y admin). Fotos de tests van a `MEDIA_TEMPORAL`.
- **Secretos** en `.env` (ignorado); `.env.example` se versiona. No hardcodear nada.
- **Migraciones**: una por cambio lógico de modelo; generarlas con `makemigrations <app>`.
- **Documentar el uso de IA** en `docs/uso-ia.md` cuando una recomendación de la IA se acepte, se cambie o se rechace, con cómo se verificó. Cuenta para el indicador 7.
- **Commits**: `feat:`/`docs:`/`fix:` en español, uno por task del plan, con los tests en verde.
