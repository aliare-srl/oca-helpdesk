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

            // MutationObserver: espera que OWL inserte la nueva fila en el DOM
            // antes de intentar enfocar, evitando la carrera con el foco de OWL.
            var tbody = table.querySelector("tbody") || table;
            var observer = new MutationObserver(function (mutations, obs) {
                var added = false;
                mutations.forEach(function (m) {
                    if (m.addedNodes.length) added = true;
                });
                if (!added) return;

                // Dar un tick extra para que OWL termine el render de la fila
                setTimeout(function () {
                    var selected = table.querySelector(".o_selected_row");
                    if (!selected) return;
                    var inp = selected.querySelector(
                        '.o_field_widget[name="name"] input'
                    );
                    if (!inp) return;
                    obs.disconnect();
                    inp.scrollIntoView({ block: "nearest" });
                    inp.focus();
                    if (inp.select) inp.select();
                }, 60);
            });
            observer.observe(tbody, { childList: true });
            // Timeout de seguridad: desconectar el observer si no se crea la fila
            setTimeout(function () { observer.disconnect(); }, 3000);

            // Disparar change para que OWL registre el valor actual antes de blur
            target.dispatchEvent(new Event("change", { bubbles: true }));
            target.blur();
            // Pequeño delay para que OWL procese el blur antes del click en Nuevo
            setTimeout(function () { btn.click(); }, 80);
        },
        true
    );
});
