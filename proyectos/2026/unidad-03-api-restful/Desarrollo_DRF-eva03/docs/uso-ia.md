# Uso de IA en el desarrollo

Usé Claude (Claude Code) como apoyo para diseñar la API, planificar la implementación y revisar la seguridad. Cada entrada anota qué pregunté, qué propuso la IA, cómo lo verifiqué y qué decidí. Las decisiones finales son mías; donde cambié o rechacé algo, queda dicho. Los tests citados existen y pasan con `python manage.py test -v 2`.

## Diseño

**1. Tema y alcance.** Pregunté si convenía hacer una API de adopción de animales en vez de repetir el dominio `Michi` de los proyectos anteriores. La IA lo recomendó porque da recursos con relaciones reales y justifica la autenticación y los permisos. Lo acepté y agregué por mi cuenta las fotos y los avistamientos. La IA propuso una versión mínima de avistamiento (sin mapa, comentarios ni notificaciones) para no inflar el alcance, y la acepté.

**2. Roles.** La IA recomendó usar solo `is_staff`. Yo pedí una jerarquía de roles. Quedó en tres niveles (adoptante, staff y admin) con `is_staff` e `is_superuser`, sin modelo propio de roles. Rechacé un cuarto nivel `voluntario` porque no aportaba. Solo el admin promueve staff, para evitar que alguien se ascienda solo (test `test_staff_no_puede_promover_a_nadie`).

**3. Estados.** La IA propuso `disponible` para el animal y yo lo cambié a `adoptable` / `adoptado`, que describe mejor lo que le pasa. Para las solicitudes aceptó el ciclo `pendiente` → `aprobada`, `rechazada` o `cancelada`, con aprobación atómica (el animal pasa a `adoptado` y se rechazan las otras pendientes). Verificado con `test_aprobar_adopta_al_animal_y_rechaza_las_demas`, `test_aprobar_resuelta_responde_409` y `test_solicitud_pendiente_duplicada_responde_400`. Descarté un tope de solicitudes pendientes por usuario: se puede agregar después.

**4. Forma de la API.** La IA propuso rutas versionadas (`/api/v1/`), recursos en plural, acciones explícitas (`/aprobar/`, `/rechazar/`) en vez de un `PATCH` libre sobre `estado`, paginación, filtros, el formato de error estándar de DRF y Swagger con `drf-spectacular`. Lo contrasté con la documentación oficial y lo acepté: las acciones explícitas evitan saltarse el ciclo de la solicitud, y el formato estándar evita inventar uno propio. Test: `test_schema_documenta_todos_los_recursos`.

**5. Plan de implementación.** La IA armó el plan paso a paso, con tests primero, siguiendo la estructura de las evaluaciones 1 y 2. Revisé esa estructura antes de aceptarlo y corregí dos cosas: el proyecto se trabaja en `main` y no en una rama nueva, y las evaluaciones anteriores ya están cerradas.

## Autenticación y seguridad

**6. Mecanismo.** La IA recomendó JWT con `simplejwt` en lugar de `TokenAuthentication` (que no se puede revocar), con refresh rotativo y blacklist, límite de intentos en login y registro, validadores de contraseña, secretos en `.env`, permisos cerrados por defecto, un registro que ignore `is_staff` y un error de login genérico. Lo verifiqué con la documentación de DRF y simplejwt y con tests: `test_login_tiene_throttling`, `test_registro_ignora_intento_de_escalada`, `test_login_no_revela_si_falla_usuario_o_clave`, `test_refresh_rota_y_el_token_viejo_deja_de_servir`, `test_logout_invalida_el_refresh`. Acepté las siete medidas y SQLite como base de datos.

**7. Duración de la sesión.** Objeté que un token que vence obliga a iniciar sesión otra vez. La IA explicó que un access corto (15 minutos) con un refresh largo y rotativo renueva la sesión sola mientras se usa, y propuso 30 días sin uso. Yo pregunté si eso era OTP: la IA aclaró que OTP es un segundo factor de un solo uso, que no tiene que ver con la duración de la sesión, y que "que el token muera al hacer login" sería sesión única, que no recomendó. Quedó refresh de 30 días con rotación y blacklist, con `logout` que lo invalida. Dejé fuera OTP y sesión única.

**8. Fotos.** La IA propuso un `ImageField` por modelo, validar extensión, tamaño (5 MB) y formato real con Pillow, y guardar con nombre aleatorio. Lo acepté, sin galería de varias fotos. Tests: `test_foto_con_contenido_que_no_es_imagen`, `test_foto_con_extension_peligrosa`, `test_foto_con_formato_no_permitido`, `test_foto_mayor_a_5mb`.

## Cosas que aparecieron al implementar y probar

**9. Tests lentos.** Los primeros 13 tests tardaban 55 segundos por el hash de contraseñas PBKDF2, que es lento a propósito. La IA propuso un hasher rápido solo cuando se corren tests (`"test" in sys.argv`). Medí 0,8 s para la suite de ese momento y confirmé que en ejecución normal sigue usando PBKDF2. Lo acepté.

**10. Registro bloqueado por un token vencido.** Al probar en Swagger, el registro devolvió 401 aunque es un endpoint público. La causa: `JWTAuthentication` rechaza un token inválido en el header `Authorization` aunque la vista sea pública, y Swagger seguía mandando uno viejo. Un cliente real con una sesión caducada habría fallado igual. Escribí primero el test que lo reproduce (`test_registro_funciona_aunque_el_cliente_mande_un_token_vencido`), vi que fallaba, y desactivé la autenticación en `registro` y `refresh`. Quedó en 201.

**11. Contraseña débil.** El registro devolvió 400 con una clave de 6 caracteres. No era un fallo: el validador de contraseñas de Django la rechazó por corta y común, que es lo que debe hacer.

**12. Revisión final.** La IA no encontró fallas graves y anotó mejoras menores que dejé fuera porque cada una agrega código sin cambiar lo esencial: el límite de 5 intentos por minuto por IP puede afectar a varias personas en una misma red al renovar tokens, un admin puede desactivarse a sí mismo, `select_for_update` no bloquea filas en SQLite (sí lo haría en MySQL o Postgres) y el nombre de usuario distingue mayúsculas. Verifiqué con la suite en verde, `makemigrations --check` sin cambios, `check --deploy` con solo avisos de HTTPS (documentados en el README) y una prueba en vivo con `runserver`.
