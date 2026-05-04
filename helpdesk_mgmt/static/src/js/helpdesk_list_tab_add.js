odoo.define("helpdesk_mgmt.list_tab_add", function (require) {
    "use strict";

    // Tab en la última celda editable de la lista de tickets:
    // guarda la fila actual y abre una nueva fila abajo con foco en Título.
    document.addEventListener(
        "keydown",
        function (e) {
            if (e.key !== "Tab" || e.shiftKey) return;

            var target = e.target;
            var cell = target.closest("td.o_data_cell");
            if (!cell) return;

            var row = cell.closest("tr.o_data_row");
            if (!row || !row.closest("table.o_helpdesk_aliare")) return;

            // Todos los inputs editables visibles en la fila actual
            var inputs = Array.from(
                row.querySelectorAll(
                    "input:not([readonly]):not([disabled]):not([type='hidden'])," +
                    "select:not([readonly]):not([disabled])"
                )
            ).filter(function (el) {
                return el.offsetParent !== null;
            });

            // Solo interceptar si el foco está en el último input de la fila
            if (!inputs.length || inputs.indexOf(target) < inputs.length - 1) return;

            e.preventDefault();
            e.stopImmediatePropagation();

            // Desfocar dispara el guardado del campo en Odoo
            target.blur();

            setTimeout(function () {
                var btn = document.querySelector(".o_list_button_add");
                if (!btn) return;

                btn.click();

                // Esperar el render de la nueva fila y enfocar el campo Título
                setTimeout(function () {
                    var newRow = document.querySelector(
                        "table.o_helpdesk_aliare .o_selected_row"
                    );
                    if (!newRow) return;

                    var nameInput = newRow.querySelector(
                        '.o_field_widget[name="name"] input'
                    );
                    if (!nameInput) return;

                    nameInput.scrollIntoView({ behavior: "smooth", block: "nearest" });
                    nameInput.focus();
                    if (nameInput.select) nameInput.select();
                }, 150);
            }, 100);
        },
        true // captura: dispara antes que cualquier listener de burbuja
    );
});
