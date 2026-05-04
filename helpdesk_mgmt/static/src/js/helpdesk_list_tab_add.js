odoo.define("helpdesk_mgmt.list_tab_add", function (require) {
    "use strict";

    document.addEventListener("keydown", function (e) {
        if (e.key !== "Tab" || e.shiftKey) return;

        var target = e.target;
        var row = target.closest("tr.o_data_row");
        if (!row) return;

        var table = row.closest("table");
        if (!table || !table.classList.contains("o_helpdesk_aliare")) return;

        // Todos los focusables visibles de la fila en orden DOM
        var all = Array.from(row.querySelectorAll(
            "input:not([type='hidden']), select, textarea, button"
        )).filter(function (el) { return el.offsetParent !== null; });

        // ¿Hay algún focusable DESPUÉS del target en la fila?
        var idx = all.indexOf(target);
        if (idx !== -1 && idx < all.length - 1) return; // no es el último, dejar pasar

        // Si target no está en la lista o es el último → interceptar
        e.preventDefault();
        e.stopImmediatePropagation();

        var btn = document.querySelector(".o_list_button_add");
        if (!btn) return;

        target.dispatchEvent(new Event("change", { bubbles: true }));

        setTimeout(function () {
            btn.click();
            _wait(table, 0);
        }, 60);

    }, true);

    function _wait(table, n) {
        if (n > 20) return;
        setTimeout(function () {
            var first = table.querySelector("tbody tr.o_data_row");
            if (!first || !first.classList.contains("o_selected_row")) {
                return _wait(table, n + 1);
            }
            var inp = first.querySelector('.o_field_widget[name="name"] input');
            if (!inp) return _wait(table, n + 1);
            inp.focus();
            inp.select && inp.select();
        }, 60 + n * 40);
    }
});
