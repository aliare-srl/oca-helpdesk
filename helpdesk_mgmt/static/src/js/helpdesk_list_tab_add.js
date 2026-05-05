/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, "helpdesk_mgmt.list_tab_add", {
    onCellKeydownEditMode(hotkey, cell, group, record) {
        if (
            hotkey !== "tab" ||
            !this.tableRef.el ||
            !this.tableRef.el.classList.contains("o_helpdesk_aliare") ||
            this.findNextFocusableOnRow(cell.parentElement, cell)
        ) {
            return this._super(...arguments);
        }

        const initialRowCount = this.tableRef.el.querySelectorAll(
            "tbody tr.o_data_row"
        ).length;

        this.add({ group });

        let attempts = 0;
        const focusNameField = () => {
            if (!this.tableRef.el) return;
            const allRows = this.tableRef.el.querySelectorAll("tbody tr.o_data_row");
            if (allRows.length > initialRowCount) {
                const inp = allRows[0].querySelector(
                    '.o_field_widget[name="name"] input'
                );
                if (inp) {
                    inp.focus();
                    inp.select();
                    return;
                }
            }
            if (++attempts < 30) setTimeout(focusNameField, 50);
        };
        setTimeout(focusNameField, 50);

        return true;
    },
});
