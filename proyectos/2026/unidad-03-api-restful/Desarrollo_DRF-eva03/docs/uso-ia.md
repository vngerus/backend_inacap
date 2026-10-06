# Uso de IA en el desarrollo (indicador 7)

Herramienta: Claude (Claude Code), usado como apoyo para diseñar la API, planificar la implementación y revisar seguridad. Cada entrada registra qué se pidió, qué recomendó la IA, cómo se verificó y qué se decidió. Las decisiones finales las tomé yo; donde cambié o rechacé algo, queda anotado.

Las entradas 1 a 9 salen de la sesión de diseño (grill-me) del 2026-10-06. Los tests citados se escriben durante la implementación; al terminar cada task hay que confirmar que existen y pasan (`python manage.py test -v 2`).

---

## 1. Dominio y alcance

- **Qué pregunté:** si convenía apuntar la API a adopción de animales en vez de repetir el dominio `Michi`.
- **Qué recomendó la IA:** adopción de animales, porque da recursos con relaciones reales (`Animal`, `SolicitudAdopcion`) y justifica la autenticación, los permisos y los códigos 409.
- **Cómo lo verifiqué:** comparé contra la pauta (productos esperados y los 7 indicadores) para ver que cada indicador tuviera algo concreto que mostrar.
- **Qué decidí:** adopté el dominio y le agregué por iniciativa propia fotos de animales y avistamientos. La IA propuso la versión mínima del avistamiento (sin mapa, comentarios ni notificaciones) para no inflar el alcance, y la acepté.

## 2. Roles y permisos

- **Qué pregunté:** quién aprueba solicitudes y cómo distinguir roles.
- **Qué recomendó la IA:** usar solo `is_staff`. Yo pedí una jerarquía (admin, staff, etc.).
- **Cómo lo verifiqué:** revisé la matriz de permisos propuesta contra los endpoints; la prueba son los tests de permisos de `cuentas`, `animales`, `adopciones` y `avistamientos`.
- **Qué decidí:** 3 niveles (adoptante < staff < admin) con `is_staff` e `is_superuser`, sin modelo de roles. Rechacé un cuarto nivel `voluntario` porque no aporta a la pauta. Regla de seguridad que se mantuvo: solo admin promueve staff, para evitar escalada de privilegios (test `test_staff_no_puede_promover_a_nadie`).

## 3. Ciclo de vida de la solicitud

- **Qué pregunté:** estados y reglas de una solicitud de adopción.
- **Qué recomendó la IA:** `pendiente → aprobada/rechazada/cancelada`, resolver solo desde `pendiente`, aprobar de forma atómica (adopta al animal y rechaza las otras pendientes), 409 si el animal ya fue adoptado, 400 si hay una pendiente duplicada.
- **Cómo lo verifiqué:** tests `test_aprobar_adopta_al_animal_y_rechaza_las_demas`, `test_aprobar_resuelta_responde_409`, `test_solicitud_pendiente_duplicada_responde_400` y la restricción única condicional en la base de datos.
- **Qué decidí:** acepté el ciclo completo. Descarté poner un tope de solicitudes pendientes por usuario (se puede agregar luego con una validación más).

## 4. Estados del animal

- **Qué pregunté:** nombre del estado inicial del animal.
- **Qué recomendó la IA:** `disponible`.
- **Cómo lo verifiqué:** lo leí contra el flujo de adopción.
- **Qué decidí:** lo cambié a `adoptable` / `adoptado`, porque describe mejor lo que le pasa al animal. La IA ajustó el resto del diseño a ese nombre.

## 5. Autenticación y seguridad (indicadores 2 y 3)

- **Qué pregunté:** qué mecanismo de autenticación y qué medidas de seguridad aplicar.
- **Qué recomendó la IA:** JWT con `simplejwt` (en vez de `TokenAuthentication`, que no se puede revocar), refresh rotativo con blacklist, throttling en login y registro, validadores de contraseña, secretos en `.env`, permisos cerrados por defecto, registro que no acepte `is_staff`, error de login genérico.
- **Cómo lo verifiqué:** documentación oficial de DRF y simplejwt, y tests: `test_login_tiene_throttling`, `test_registro_ignora_intento_de_escalada`, `test_login_no_revela_si_falla_usuario_o_clave`, `test_refresh_rota_y_el_token_viejo_deja_de_servir`, `test_logout_invalida_el_refresh`.
- **Qué decidí:** acepté las 7 medidas con SQLite como base de datos. La IA propuso un access de 15 minutos con un refresh más largo; ver entrada 6 para lo que cambié.

## 6. Duración de la sesión

- **Qué pregunté:** si un token que expira obliga al usuario a iniciar sesión otra vez ("no vale la pena así").
- **Qué recomendó la IA:** mantener el access corto (15 minutos) y un refresh largo con rotación, de modo que la sesión se renueve sola mientras se usa; propuso 30 días sin uso.
- **Cómo lo verifiqué:** pregunté si eso era OTP. La IA aclaró que OTP es un segundo factor de un solo uso, que no tiene relación con la duración de la sesión, y que "el token muere al hacer login" sería sesión única, que no recomendó. Contrasté con la documentación de simplejwt (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`).
- **Qué decidí:** refresh de 30 días con rotación y blacklist, `logout` que lo invalida, y dejé fuera OTP y sesión única.

## 7. Forma de la API (indicadores 4, 5 y 6)

- **Qué pregunté:** estructura de rutas, respuestas JSON y errores.
- **Qué recomendó la IA:** `/api/v1/`, recursos en plural, acciones explícitas (`/aprobar/`, `/rechazar/`) en vez de un `PATCH` libre sobre `estado`, paginación, filtros, formato de error estándar de DRF y Swagger con `drf-spectacular`.
- **Cómo lo verifiqué:** documentación oficial de DRF y drf-spectacular, y el test `test_schema_documenta_todos_los_recursos`.
- **Qué decidí:** acepté todo. Las acciones explícitas evitan que se salte el ciclo de la solicitud; el formato de error estándar evita inventar uno propio.

## 8. Fotos de animales y avistamientos

- **Qué pregunté:** cómo subir imágenes de forma segura.
- **Qué recomendó la IA:** un `ImageField` por modelo, validar tipo, extensión y tamaño (5 MB), verificar con Pillow y guardar con nombre UUID.
- **Cómo lo verifiqué:** tests `test_foto_con_contenido_que_no_es_imagen`, `test_foto_con_extension_peligrosa`, `test_foto_con_formato_no_permitido`, `test_foto_mayor_a_5mb`.
- **Qué decidí:** acepté la propuesta, sin galería de varias fotos (suma otro modelo y no mejora la nota).

## 9. Plan de implementación y estructura

- **Qué pregunté:** cómo organizar el trabajo para no cometer errores y seguir el patrón de las evaluaciones 1 y 2.
- **Qué recomendó la IA:** un plan con tareas pequeñas, test primero y cada una mapeada a un indicador, con `CLAUDE.md` y `docs/superpowers/plans/` como en los otros proyectos; 4 apps por recurso; `requirements.txt` propio del proyecto.
- **Cómo lo verifiqué:** revisé la estructura y el plan de `Desarrollo_Django-eva02` antes de aceptar. Yo corregí que el proyecto se trabaja en `main` y no en una rama nueva, y que las evaluaciones 1 y 2 ya están cerradas.
- **Qué decidí:** seguir el patrón de los proyectos anteriores, con la carpeta nueva dentro de `proyectos/2026/`.

---

## Entradas de la implementación

Agregar aquí una entrada (con los cuatro campos) por cada problema real que aparezca al ejecutar el plan: un error de configuración, una recomendación de la IA que haya que corregir, una vulnerabilidad detectada en una revisión de seguridad. Estas entradas son las que muestran contraste crítico con la IA, que es lo que pide el nivel Destacado del indicador 7.
