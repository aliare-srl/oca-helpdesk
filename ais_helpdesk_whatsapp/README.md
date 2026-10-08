# ais_helpdesk_whatsapp

Agrega a la Mesa de Ayuda de Odoo la pantalla donde el equipo ve y atiende las conversaciones de WhatsApp que maneja el agente de IA (proyecto `AgenteIA-MesadeAyuda-Odoo`). El módulo no guarda la conversación real: la fuente de verdad es ese servicio externo, acá solo se muestra una copia liviana y se disparan las acciones a través de su API.

## Funcionalidad

- Menú **Helpdesk → Conversaciones de WhatsApp**: lista de conversaciones, con las urgentes y las que esperan a una persona resaltadas.
- Por conversación: **Actualizar** (trae estado y mensajes nuevos), **Tomar** (pausa la IA), **Responder** (manda un mensaje real por WhatsApp), **Devolver a la IA**, **Cerrar**.
- Los mensajes se muestran en el chatter nativo de Odoo (igual que el historial de un ticket), marcados Cliente / IA / Persona.
- Vínculo directo al ticket del Helpdesk relacionado, cuando existe.
- Menú **Helpdesk → Iniciar conversación**: para escribirle primero a un cliente con una plantilla aprobada por Meta.
- Sincronización automática de la lista cada 2 minutos (no de los mensajes, para no recargar innecesariamente: esos se traen al abrir o actualizar una conversación puntual).

## Instalación

Depende de `helpdesk_mgmt`. Sin configuración adicional en el `__manifest__`; usa `requests`, ya incluido en el entorno de Odoo.

## Configuración

**Ajustes → Mesa de Ayuda WhatsApp** (solo administradores de Helpdesk):

- **URL del servicio**: la del `AgenteIA-MesadeAyuda-Odoo` desplegado (ej. `https://mesaayuda.mochipa.com.ar`), sin la barra final.
- **Clave de la API**: la `PANEL_API_KEY` configurada en el `.env` de ese servicio.

## Uso

1. Un cliente escribe por WhatsApp; la IA responde sola o escala.
2. Cuando una conversación necesita a una persona, aparece en **Conversaciones de WhatsApp** marcada "Esperando a un humano" (o "Urgente").
3. Se abre, se apreta **Tomar** y después **Responder** para escribirle al cliente. Mientras una persona la tiene tomada, la IA no contesta; si pasan 2 horas sin que nadie responda, vuelve sola a la IA (configurable en el servicio).
4. **Devolver a la IA** o **Cerrar** cuando termina.
5. Para escribirle primero a un cliente (sin que haya escrito antes), **Iniciar conversación** con una plantilla ya aprobada por Meta.

## Detalle técnico

- `models/whatsapp_conversation.py`: `ais.whatsapp.conversation`, hereda `mail.thread` para reusar el chatter como historial de mensajes. `ticket_id` es un `Many2one` calculado al `helpdesk.ticket` real (el id que guarda el servicio ya es el id del ticket en esta misma base, porque el agente escribe directo por XML-RPC).
- `services/agent_client.py`: único punto de acceso a la API del servicio (`requests`), con errores traducidos a `UserError`.
- `wizards/`: ventanas para responder e iniciar conversación.
- `data/ir_cron.xml`: sincroniza la lista cada 2 minutos; no corre si el servicio todavía no está configurado.
- No usa JavaScript (OWL): primera versión con vistas estándar. El diseño visual (tres columnas, actualización en vivo) queda para una segunda etapa.
