/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, "helpdesk_mgmt.list_tab_add", {
    onCellKeydownEditMode(hotkey, cell, group, record) {
        // Solo actuar en nuestra tabla y cuando Tab llega al último campo editable
        if (
            hotkey !== "tab" ||
            !this.tableRef.el ||
            !this.tableRef.el.classList.contains("o_helpdesk_aliare") ||
            this.findNextFocusableOnRow(cell.parentElement, cell)
        ) {
            return this._super(...arguments);
        }

        // Crear nueva fila arriba (editable="top") en lugar de ir al registro siguiente
        this.add({ group });

        // Forzar foco en el campo Título de la fila nueva (primer tr seleccionado)
        setTimeout(() => {
            const firstRow = this.tableRef.el.querySelector(
                "tbody tr.o_data_row.o_selected_row"
            );
            if (!firstRow) return;
            const inp = firstRow.querySelector('.o_field_widget[name="name"] input');
            if (inp) {
                inp.focus();
                inp.select();
            }
        }, 100);

        return true; // le dice a Odoo que ejecute ev.preventDefault() + ev.stopPropagation()
    },
});
