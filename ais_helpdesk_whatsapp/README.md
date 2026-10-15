# ais_helpdesk_whatsapp

Agrega a la Mesa de Ayuda de Odoo la pantalla donde el equipo ve y atiende las conversaciones de WhatsApp que maneja el agente de IA (proyecto `AgenteIA-MesadeAyuda-Odoo`). El módulo no guarda la conversación real: la fuente de verdad es ese servicio externo, acá solo se muestra una copia liviana y se disparan las acciones a través de su API.

## Funcionalidad

- Menú **Helpdesk → Conversaciones de WhatsApp**: pantalla propia (OWL) de tres columnas — lista, chat, ficha del cliente/ticket.
- Lista de conversaciones con búsqueda, filtro por rango de fecha (por defecto, hoy) y 5 pestañas de estado: **Esperando**, **IA**, **Persona**, **Cerradas**, **Todas**. Dentro de cada estado, ordenadas por hora de ingreso más reciente primero; al cerrarse, una conversación pasa a "Cerradas".
- El panel de mensajes baja solo al último mensaje cuando entran o salen mensajes (si estás leyendo mensajes viejos, no te mueve).
- Cada conversación de la lista muestra la fecha y hora (dd/mm hh:mm a. m./p. m.) de su último mensaje.
- **Búsqueda general**: el campo de arriba de la lista busca por cliente, número **y texto de los mensajes**, en todas las conversaciones (también cerradas) dentro del rango de fechas; muestra un fragmento y la cantidad de coincidencias, sin importar la pestaña elegida. Pide al servicio `GET /api/messages/search` (mín. 2 letras, hasta 50 conversaciones; la búsqueda general distingue tildes, la de dentro de la conversación no).
- **Búsqueda dentro de la conversación**: barra sobre los mensajes; resalta las coincidencias, muestra "2 de 5", ↑/↓ (o Enter / Shift+Enter) para saltar entre ellas, Esc para cerrar. Si se abre una conversación desde la búsqueda general, ya queda buscada. Mientras hay una búsqueda abierta el panel no baja solo.
- **Tickets**: el servicio ya no crea el ticket al empezar el chat, sino cuando el cliente cuenta su consulta o error (o cuando la conversación pasa a una persona). Si se cierra con resolución una conversación que no tiene ticket, se crea uno directamente en "Hecho" (empresa, mensajes del cliente y resolución) en `controllers/main.py`.
- **Datos de la empresa cliente** (contacto de tipo empresa > solapa "Mesa de ayuda", `models/res_partner.py`): versión de Odoo instalada (lista 11.0 a 19.0), plan de soporte (lista que se administra en Helpdesk > Configuración > Planes de soporte, modelo `ais.support.plan`, con nombre y observaciones de qué incluye), tickets por mes (0 = ilimitado) y tickets usados del mes. La URL de su Odoo es el campo nativo "Sitio web". El servicio lee estos campos al identificar al cliente (versión, plan, si su sistema responde) y no registra más consultas si ya usó todos los tickets del mes. Cuentan los tickets de la empresa y de todos sus contactos, creados en el mes (hora de Argentina) y ya resueltos (etapa cerrada; los cancelados y rechazados no cuentan).
- **Categorías del ticket** (Ajustes > Mesa de Ayuda): "Categorías de consultas" (lista, por ejemplo consultas, reclamos y errores de Odoo: solo los tickets de estas categorías cuentan para el tope mensual; vacía = cuentan todos) y "Categorías de urgencias" (lista; viene con la categoría "Urgente" que crea el módulo; no cuentan para el tope). La IA elige la categoría de cada ticket entre las de ambas listas según lo que plantea el cliente; si no elige, usa la primera de la lista (menor id). Las de urgencias nunca suman al tope. Parámetros `ais_helpdesk_whatsapp.quota_category_ids` y `urgent_category_ids` (ids separados por coma).
- **Conversación tomada = de una sola persona**: mientras alguien la tiene tomada, nadie más puede tomarla, responderla, devolverla ni cerrarla (el servicio lo valida con el usuario de Odoo que actúa; el tablero oculta los botones). Quien la tiene puede **Devolver a la IA**, **Devolver a esperando persona** (queda sin responsable el ticket hasta que alguien la tome), **Delegar** o **Cerrar**. Un administrador (Ajustes o Responsable de Mesa de Ayuda) puede **Soltarla** a "Esperando a un humano" si quien la tiene no está. Si vence la pausa, también se libera al dueño.
- **Delegar**: se elige un usuario con acceso a la mesa de ayuda; hasta que acepte, la conversación sigue siendo de quien la tenía. El delegado ve un aviso en el tablero y recibe una notificación de Odoo; al **Aceptar** pasa a ser suya (y el ticket se le asigna), con **Rechazar** o si quien delegó **Cancela**, queda como estaba. Desde la misma pantalla se puede abrir el **chat de Odoo** con el usuario (`messaging.openChat`). Rutas nuevas del controlador: `return_to_waiting`, `team`, `delegate`, `cancel_delegation`, `accept_delegation`, `reject_delegation`; `agent_client` manda siempre `user_id`, `user_name` e `is_admin`.
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

- **Desactivar el agente de IA**: si se marca, ninguna conversación nueva la contesta la IA, pasan directo a esperar a una persona (avisándole al cliente). No afecta a las que ya está atendiendo alguien. Con el agente desactivado se oculta "Devolver a la IA" (formulario y tablero), y si vence el plazo de una conversación tomada, pasa a "Esperando a un humano" en vez de volver a la IA. El tablero lee el valor al abrirse (hay que recargar la página para ver un cambio).
- **URL del servicio** y **clave de la API**: las del `AgenteIA-MesadeAyuda-Odoo` desplegado y su `PANEL_API_KEY`.
- **Usuario de la IA**: a nombre de quién queda un ticket mientras lo atiende la IA.
- **Minutos de inactividad del cliente para cerrar solo**: por defecto 30. Cuenta desde el último mensaje del cliente y aplica a toda conversación abierta (también las que esperan a una persona). Al cerrar se le avisa: "…al no haber recibido respuesta durante los últimos N minutos, damos por finalizada esta atención…".
- **Segundos entre actualizaciones de la pantalla**: por defecto 4.
- **Minutos entre avisos de conversaciones esperando**: por defecto 15. Mientras haya conversaciones "Esperando a un humano", se avisa cada este tiempo; se repite solo mientras la cola no se vacíe. 0 lo desactiva.
- **Equipo para avisos de conversaciones esperando**: a qué equipo de Helpdesk avisar. El aviso va por mail y WhatsApp a cada miembro del equipo (según el mail/móvil que tengan cargado en su contacto), menos el usuario de la IA. El WhatsApp necesita además una plantilla aprobada por Meta configurada en el servicio.
- **Avisos al cliente en espera** (dos, ambos con activar, texto y minutos): se mandan por WhatsApp a las conversaciones en "Esperando a un humano" y quedan en el historial. El primero sale al cumplirse los minutos desde que la conversación empezó a esperar y luego se repite cada ese tiempo; al ser tomada, devuelta a la IA o cerrada, deja de recibirlos. **Aviso 1** (operadores ocupados, 5 min por defecto) y **Aviso 2** (demora, 10 min por defecto). Si el 2 está activo tiene prioridad y el 1 no se manda. Ambos vienen desactivados. Son texto libre: solo llegan si el cliente escribió en las últimas 24 h (si no, se saltea y se reintenta en el próximo plazo).
- **Urgencias**: cuando una conversación urgente queda en "Esperando a un humano", el tablero muestra arriba un banner rojo con parpadeo suave (sin sonido; se desactiva con "reducir movimiento" del navegador), con cliente, desde cuándo espera y un botón **Ver** que abre la más antigua; la fila de la lista lleva borde rojo. Desaparece al tomarla, devolverla a la IA o cerrarla. Además, **una sola vez** por conversación y a cualquier hora, el servicio avisa por mail y WhatsApp (plantilla de urgencias) a los miembros del equipo de "Equipo para avisos de conversaciones esperando"; sin equipo configurado no manda nada. Es independiente del aviso a la guardia (fuera de horario).
- **Nombre y número de conversación**: la conversación se muestra como "Nombre de WhatsApp - Empresa" (solo el nombre si todavía no hay empresa identificada), en la lista, la cabecera y cada mensaje del cliente. En la lista y en la cabecera del chat, el nombre arranca con el número de la conversación (`#83`, su id) para poder referirse a ella, por ejemplo al delegarla. El buscador acepta `#83` (solo esa conversación, de cualquier estado) o un número corto de hasta 6 dígitos, además de cliente, teléfono y texto de los mensajes; respeta el filtro de fechas.

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
- **Filtro por fechas del tablero**: compara con la fecha **local** del último mensaje (la misma que muestra la lista), no con la fecha UTC; antes una conversación de la noche aparecía en el día siguiente.
- **Nuevos requerimientos**: lo que el cliente pide y Odoo no hace (o una necesidad sin respuesta válida) lo registra la IA con la tool `registrar_nuevo_requerimiento`: el ticket va con la **categoría de nuevos requerimientos** (se crea "Nuevo requerimiento" al instalar) y se asigna al **responsable de nuevos requerimientos**; ambos se eligen en Ajustes > Mesa de ayuda (parámetros `ais_helpdesk_whatsapp.requirement_category_id` y `requirement_user_id`). Al cliente se le avisa que lo evalúa el sector de desarrollo y que se van a comunicar para decirle si es factible y qué costo tiene. No cuenta para el tope mensual (no está entre las categorías de consultas) y, cuando la conversación se cierra, el ticket **queda abierto** para su evaluación. Si el parámetro de categoría ya existe, la carga inicial no lo pisa (`noupdate`).
