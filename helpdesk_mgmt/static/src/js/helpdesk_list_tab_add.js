odoo.define("helpdesk_mgmt.list_tab_add", function (require) {
    "use strict";

    document.addEventListener("keydown", function (e) {
        if (e.key !== "Tab" || e.shiftKey) return;

        var target = e.target;

        // Debe estar dentro de nuestra tabla
        var table = target.closest("table.o_helpdesk_aliare");
        if (!table) return;

        // Debe estar dentro de la celda del campo stage_id (último campo editable)
        if (!target.closest('[name="stage_id"]')) return;

        e.preventDefault();
        e.stopImmediatePropagation();

        var btn = document.querySelector(".o_list_button_add");
        if (!btn) return;

        target.dispatchEvent(new Event("change", { bubbles: true }));

        setTimeout(function () {
            btn.click();
            _waitForNewRow(table, 0);
        }, 60);
    }, true);

    function _waitForNewRow(table, attempt) {
        if (attempt > 20) return;
        setTimeout(function () {
            var tbody = table.querySelector("tbody");
            if (!tbody) { _waitForNewRow(table, attempt + 1); return; }

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
