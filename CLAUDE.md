# PROYECTO: oca-helpdesk — Odoo 15 CE
## STACK
- Odoo 15 Community Edition
- Módulos: helpdesk_mgmt + helpdesk_mgmt_rating
- Python / XML / JS (legacy odoo.define)

## DEPLOY
- `~/deploy.sh helpdesk <modulo>`
- Container: `odoo15_cont` | BD: `demo`

## DEPLOY AUTOMÁTICO
- Al finalizar cada desarrollo, verificar módulo trabajado
- Preguntar siempre: "¿Ejecuto el deploy? ~/deploy.sh helpdesk <modulo>"
- Ejecutar solo con confirmación explícita del usuario

## ADVERTENCIAS CONOCIDAS
- JS: sintaxis legacy `odoo.define` — mezclar con `@odoo-module` rompe el bundle silenciosamente
- Notificaciones portal: RPC polling (no longpolling — Docker/Nginx no lo soporta)
- Borrado de tickets: bloqueado por override de unlink (solo archivar)
- Rating: usa `send_mail` directo, no `rating_send_request` (evita duplicados)

## VERSIONADO
- Formato: `15.0.X.Y.Z` en `__manifest__.py`
- Cambios documentados en README (sección Changelog)
