odoo.define("helpdesk_mgmt.list_tab_add", function (require) {
    "use strict";

    document.addEventListener(
        "keydown",
        function (e) {
            if (e.key !== "Tab" || e.shiftKey) return;

            var target = e.target;
            var cell = target.closest("td.o_data_cell");
            if (!cell) return;

            var row = cell.closest("tr.o_data_row");
            if (!row) return;

            var table = row.closest("table.o_helpdesk_aliare");
            if (!table) return;

            var inputs = Array.from(
                row.querySelectorAll(
                    "input:not([readonly]):not([disabled]):not([type='hidden'])," +
                    "select:not([readonly]):not([disabled])"
                )
            ).filter(function (el) { return el.offsetParent !== null; });

            if (!inputs.length || inputs.indexOf(target) < inputs.length - 1) return;

            e.preventDefault();
            e.stopImmediatePropagation();

            var btn = document.querySelector(".o_list_button_add");
            if (!btn) return;

            // Registrar el valor actual antes de salir del campo
            target.dispatchEvent(new Event("change", { bubbles: true }));
            target.blur();

            setTimeout(function () {
                btn.click();
                _focusNewRow(table, 0);
            }, 80);
        },
        true
    );

    function _focusNewRow(table, attempt) {
        if (attempt > 20) return;
        setTimeout(function () {
            // La nueva fila queda en primer lugar (editable="top") y es la seleccionada
            var tbody = table.querySelector("tbody");
            if (!tbody) { _focusNewRow(table, attempt + 1); return; }

            var selected = tbody.querySelector("tr.o_data_row.o_selected_row");
            if (!selected) { _focusNewRow(table, attempt + 1); return; }

            // Verificar que es la primera fila (no un registro viejo seleccionado)
            var firstRow = tbody.querySelector("tr.o_data_row");
            if (selected !== firstRow) { _focusNewRow(table, attempt + 1); return; }

            var inp = selected.querySelector('.o_field_widget[name="name"] input');
            if (!inp) { _focusNewRow(table, attempt + 1); return; }

            inp.focus();
            if (inp.select) inp.select();
        }, 50 + attempt * 40);
    }
});
