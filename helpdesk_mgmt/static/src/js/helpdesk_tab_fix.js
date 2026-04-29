odoo.define("helpdesk_mgmt.tab_navigation", function (require) {
    "use strict";

    // Intercepta el TAB en el editor HTML de description ANTES de que el editor
    // Odoo lo consuma (fase de captura). stopImmediatePropagation garantiza que
    // ningún otro listener en document (incluido web_editor) procese el evento.
    document.addEventListener(
        "keydown",
        function (e) {
            if (e.key !== "Tab" || e.shiftKey) {
                return;
            }
            var target = e.target;
            if (!target.isContentEditable) {
                return;
            }
            var htmlWidget = target.closest(".o_field_html");
            if (!htmlWidget) {
                return;
            }
            var form = htmlWidget.closest(".o_form_view");
            if (!form) {
                return;
            }

            e.preventDefault();
            e.stopImmediatePropagation();

            // Destino: campo partner_id (Cliente)
            var nextInput = form.querySelector(
                '.o_field_widget[name="partner_id"] input'
            );

            // Fallback: primer input editable visible del formulario
            if (!nextInput || nextInput.offsetParent === null) {
                nextInput = form.querySelector(
                    'input.o_input:not([readonly]):not([disabled])'
                );
            }

            if (nextInput) {
                nextInput.focus();
                if (nextInput.select) {
                    nextInput.select();
                }
            }
        },
        true // fase de captura: dispara antes que cualquier listener de burbuja
    );
});
