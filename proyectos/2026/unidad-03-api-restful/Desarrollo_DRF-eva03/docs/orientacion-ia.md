# Cómo orientamos el proyecto con IA

Antes de escribir código, el proyecto se orientó con una conversación guiada con IA (Claude Code, plugin Superpowers). Estas fueron las preguntas y lo que se decidió en cada una.

| Pregunta | Decisión |
|---|---|
| ¿Qué dominio usamos? | Adopción de animales, con fotos y avistamientos, en vez de repetir el de los proyectos anteriores |
| ¿Quién aprueba las solicitudes y cómo se distinguen los roles? | Tres roles jerárquicos: adoptante, staff y admin, con `is_staff` e `is_superuser` de Django |
| ¿Quién puede ascender a otros? | Solo el admin, para que nadie se ascienda solo |
| ¿Cómo es el ciclo de una solicitud? | `pendiente` pasa a `aprobada`, `rechazada` o `cancelada`; aprobar adopta al animal y rechaza las demás pendientes |
| ¿Cómo se llaman los estados del animal? | `adoptable` y `adoptado` |
| ¿Hasta dónde llega el avistamiento? | Reportar con foto, verificar y convertir en animal. Sin mapa, comentarios ni notificaciones |
| ¿Qué usuario y qué campos? | El usuario por defecto de Django, con email obligatorio; campos mínimos en cada modelo |
| ¿Cómo se autentica? | JWT con refresh rotativo, para poder invalidar tokens al cerrar sesión |
| ¿Cuánto dura la sesión sin que el usuario tenga que volver a entrar? | Access de 15 minutos y refresh de 30 días, que se renueva solo mientras se usa |
| ¿Qué medidas de seguridad llevan los endpoints? | Límite de intentos, validación de contraseñas, secretos en `.env`, permisos cerrados por defecto, fotos verificadas |
| ¿Cómo son las rutas, las respuestas y los errores? | `/api/v1/`, recursos en plural, acciones como `POST` (`/aprobar/`), paginación, errores estándar de DRF y Swagger |
| ¿Cómo se prueba? | Tests automáticos con `APITestCase` y pruebas manuales en Swagger |
| ¿Cómo se organiza el repo? | Carpeta independiente en `proyectos/2026/`, trabajo en `main`, una app por recurso, SQLite y `requirements.txt` propio |

Después, el plan de implementación se escribió por tareas pequeñas, con el test primero, y se ejecutó tarea por tarea. Las pruebas en Swagger mostraron un fallo real (el registro rechazaba un token vencido) que se corrigió con un test.
