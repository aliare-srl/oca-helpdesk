# ais_helpdesk_whatsapp

Agrega a la Mesa de Ayuda de Odoo la pantalla donde el equipo ve y atiende las conversaciones de WhatsApp que maneja el agente de IA (proyecto `AgenteIA-MesadeAyuda-Odoo`). El módulo no guarda la conversación real: la fuente de verdad es ese servicio externo, acá solo se muestra una copia liviana y se disparan las acciones a través de su API.

## Funcionalidad

- Menú **Helpdesk → Conversaciones de WhatsApp**: pantalla propia (OWL) de tres columnas — lista, chat, ficha del cliente/ticket.
- Lista de conversaciones con búsqueda, filtro por rango de fecha (por defecto, hoy) y 5 pestañas de estado: **Esperando**, **IA**, **Persona**, **Cerradas**, **Todas**. Dentro de cada estado, ordenadas por hora de ingreso más reciente primero; al cerrarse, una conversación pasa a "Cerradas".
- Por conversación: **Tomar** (pausa la IA y asigna el ticket a quien la toma, con historial de reasignaciones), **Responder** (solo mientras la tiene tomada una persona), **Devolver a la IA**, **Cerrar con resolución** (la resolución queda en la descripción del ticket, como base de casos resueltos).
- Las imágenes que manda el cliente se ven directo en el chat (no solo como adjunto genérico); otros archivos quedan como link para abrir.
- Si el cliente no vuelve a escribir dentro del tiempo configurado, la conversación se cierra sola y se avisa por WhatsApp.
- Botón **Abrir ticket** (header del chat, visible también en celular, y en la ficha del cliente).
- Desde la ficha de un ticket del Helpdesk: botón **Iniciar WhatsApp** si el contacto tiene celular cargado y todavía no hay conversación, con el mismo modal de "Iniciar conversación" (vincula la conversación nueva a ese ticket).
- Menú **Helpdesk → Iniciar conversación**: para escribirle primero a cualquier cliente con una plantilla aprobada por Meta.

## Instalación

Depende de `helpdesk_mgmt`. Sin configuración adicional en el `__manifest__`; usa `requests`, ya incluido en el entorno de Odoo.

## Configuración

**Ajustes → Mesa de Ayuda** (solo administradores de Helpdesk):

- **URL del servicio** y **clave de la API**: las del `AgenteIA-MesadeAyuda-Odoo` desplegado y su `PANEL_API_KEY`.
- **Usuario de la IA**: a nombre de quién queda un ticket mientras lo atiende la IA.
- **Minutos de inactividad del cliente para cerrar solo**: por defecto 30.
- **Segundos entre actualizaciones de la pantalla**: por defecto 4.
- **Minutos entre avisos de conversaciones esperando**: por defecto 15. Mientras haya conversaciones "Esperando a un humano", se avisa cada este tiempo; se repite solo mientras la cola no se vacíe. 0 lo desactiva.
- **Equipo para avisos de conversaciones esperando**: a qué equipo de Helpdesk avisar. El aviso va por mail y WhatsApp a cada miembro del equipo (según el mail/móvil que tengan cargado en su contacto), menos el usuario de la IA. El WhatsApp necesita además una plantilla aprobada por Meta configurada en el servicio.

## Uso

1. Un cliente escribe por WhatsApp; la IA responde sola, deriva a comercial o escala a una persona.
2. Cuando una conversación necesita a alguien, aparece en la pestaña **Esperando**.
3. Se abre, se apreta **Tomar** y después se responde. Mientras una persona la tiene tomada, la IA no contesta; si pasa el tiempo configurado sin que nadie responda, vuelve sola a la IA.
4. **Devolver a la IA** o **Cerrar con resolución** cuando termina (la resolución escrita ahí queda en el ticket).
5. Para escribirle primero a un cliente, **Iniciar conversación** (desde el menú, o desde el botón del ticket si ya tiene WhatsApp cargado) con una plantilla aprobada por Meta.

## Detalle técnico

- `controllers/main.py`: rutas JSON que consume la pantalla OWL (proxy fino a `services/agent_client.py`), más una ruta HTTP (no JSON-RPC) para servir el adjunto real de un mensaje.
- `services/agent_client.py`: único punto de acceso a la API del servicio (`requests`), con errores traducidos a `UserError`.
- `static/src/js/whatsapp_dashboard.js`, `static/src/xml/whatsapp_dashboard.xml`, `static/src/scss/whatsapp_dashboard.scss`: la pantalla OWL (`ir.actions.client` con tag `ais_whatsapp_dashboard`).
- `models/helpdesk_ticket.py`: `whatsapp_conversation_remote_id` (lo escribe el servicio al crear el ticket), botones para abrir/iniciar la conversación desde el ticket, `user_id` con tracking para ver el historial de reasignaciones.
- `models/res_config_settings.py`: los parámetros de Ajustes, como `ir.config_parameter`.
- `wizards/whatsapp_start_wizard.py`: ventana para iniciar una conversación nueva.
- `data/ir_cron.xml`: sincroniza la lista cada 2 minutos; no corre si el servicio todavía no está configurado.
