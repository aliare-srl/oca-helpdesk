/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, "helpdesk_mgmt.list_tab_add", {
    onCellKeydownEditMode(hotkey, cell, group, record) {
        if (
            hotkey === "tab" &&
            this.tableRef.el &&
            this.tableRef.el.classList.contains("o_helpdesk_aliare") &&
            !this.findNextFocusableOnRow(cell.parentElement, cell)
        ) {
            // Último campo de la fila: crear fila nueva arriba en vez de ir al registro siguiente
            this.add({ group });
            return true;
        }
        return this._super(...arguments);
    },
});
