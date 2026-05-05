/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

/**
 * Patch del botón "Guardar" en la vista lista del Helpdesk.
 *
 * Problema original:
 *   - onClickSave() llamaba a this._super() que NO existe en el sistema de
 *     patch OWL de Odoo 15. Usar _super en este contexto lanza un error
 *     silencioso y el método original nunca se ejecuta para vistas que NO
 *     son de helpdesk, rompiendo el guardado en cualquier otra lista.
 *   - Si editedRecord era null (el usuario hizo clic en Guardar sin tener
 *     ninguna fila en edición), la función retornaba undefined en lugar de
 *     delegar al comportamiento original.
 *   - No había manejo de errores: si save() o load() fallaban, la UI
 *     quedaba en estado inconsistente sin feedback al usuario.
 *
 * Solución:
 *   1. Guardar la referencia al método original ANTES del patch y llamarlo
 *      explícitamente en lugar de _super (patrón correcto en OWL/Owl patch).
 *   2. Salir temprano hacia el original cuando la vista no es helpdesk.
 *   3. Si no hay fila en edición, delegar también al original (por si el
 *      controller tiene lógica propia de guardado batch).
 *   4. Envolver todo en try/catch para no romper la UI en caso de error.
 *   5. Detectar la vista mediante this.props.resModel como respaldo adicional
 *      por si el DOM aún no renderizó la tabla al momento del click.
 */

// Capturamos el método original ANTES de patchear, para poder llamarlo
// de forma segura sin depender de _super (que no existe en OWL patches).
const _originalOnClickSave = ListController.prototype.onClickSave;

patch(ListController.prototype, "helpdesk_mgmt.list_save_reload", {

    async onClickSave() {
        // --- Detección de la vista helpdesk ---
        // Estrategia 1: clase CSS en la tabla (más específica, requiere DOM listo)
        const tableHasClass =
            this.rootRef &&
            this.rootRef.el &&
            this.rootRef.el.querySelector("table.o_helpdesk_aliare");

        // Estrategia 2: modelo del recurso (fallback si el DOM aún no renderizó)
        const isHelpdeskModel =
            this.props &&
            this.props.resModel === "helpdesk.ticket";

        const isHelpdeskView = tableHasClass || isHelpdeskModel;

        // Si no es la vista de helpdesk, ejecutar comportamiento estándar de Odoo.
        if (!isHelpdeskView) {
            return _originalOnClickSave.apply(this, arguments);
        }

        // --- Lógica específica helpdesk ---
        const root = this.model && this.model.root;
        const editedRecord = root && root.editedRecord;

        // Sin fila en edición → delegar al original (puede haber lógica de
        // guardado batch u otras acciones del controller que no debemos omitir).
        if (!editedRecord) {
            return _originalOnClickSave.apply(this, arguments);
        }

        try {
            const saved = await editedRecord.save();

            if (saved) {
                // Recarga la lista para que se reordene por create_date desc
                // y los tickets recién creados queden al tope de la grilla.
                await root.load();
                this.model.notify();
            }
            // Si saved === false el registro tenía errores de validación;
            // Odoo ya muestra los mensajes de error inline, no hacemos nada más.

        } catch (error) {
            // Error inesperado (ej: problema de red, error de servidor).
            // Re-lanzamos para que el bus de errores de Odoo lo capture y
            // muestre la notificación de error estándar al usuario.
            console.error("[helpdesk_mgmt] Error al guardar/recargar la lista:", error);
            throw error;
        }
    },
});
