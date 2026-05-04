odoo.define("helpdesk_mgmt.list_tab_add", function (require) {
    "use strict";

    document.addEventListener("keydown", function (e) {
        if (e.key !== "Tab" || e.shiftKey) return;

        var target = e.target;

        // Solo actuar dentro de nuestra tabla específica
        var table = target.closest("table.o_helpdesk_aliare");
        if (!table) return;

        var row = target.closest("tr.o_data_row");
        if (!row) return;

        // Todos los elementos focusables visibles en la fila (incluyendo readonly y botones)
        var focusables = Array.from(
            row.querySelectorAll(
                "input:not([type='hidden']), select, textarea, button:not([disabled])"
            )
        ).filter(function (el) {
            return el.offsetParent !== null && el.tabIndex !== -1;
        });

        if (!focusables.length) return;

        var idx = focusables.indexOf(target);

        // Si el target no se encuentra o no es el último elemento, Tab navega normal
        if (idx === -1 || idx < focusables.length - 1) return;

        e.preventDefault();
        e.stopImmediatePropagation();

        var btn = document.querySelector(".o_list_button_add");
        if (!btn) return;

        // Registrar el valor actual. NO llamar blur(): dispara la lógica de OWL
        // que mueve el foco a la fila siguiente antes de nuestro click.
        target.dispatchEvent(new Event("input", { bubbles: true }));
        target.dispatchEvent(new Event("change", { bubbles: true }));

        setTimeout(function () {
            btn.click();
            _waitForNewRow(table, 0);
        }, 50);

    }, true);

    function _waitForNewRow(table, attempt) {
        if (attempt > 25) return;
        setTimeout(function () {
            var tbody = table.querySelector("tbody");
            if (!tbody) { _waitForNewRow(table, attempt + 1); return; }

            // Con editable="top" la nueva fila queda primera Y es la seleccionada
            var firstRow = tbody.querySelector("tr.o_data_row");
            if (!firstRow || !firstRow.classList.contains("o_selected_row")) {
                _waitForNewRow(table, attempt + 1);
                return;
            }

            var inp = firstRow.querySelector('.o_field_widget[name="name"] input');
            if (!inp) { _waitForNewRow(table, attempt + 1); return; }

            inp.focus();
            if (inp.select) inp.select();
        }, 60 + attempt * 40);
    }
});
