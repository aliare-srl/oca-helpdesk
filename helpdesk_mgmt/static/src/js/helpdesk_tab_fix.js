odoo.define("helpdesk_mgmt.tab_navigation", function (require) {
    "use strict";

    // Intercepta el TAB en el editor HTML de description ANTES de que el editor
    // Odoo lo consuma (fase de captura). Al salir, enfoca el campo partner_id
    // (Cliente), ya que ese campo queda ANTES de description en el DOM y la
    // estrategia genérica de "siguiente en el DOM" no lo alcanza.
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
            e.stopPropagation();

            // Destino principal: campo partner_id (Cliente)
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
                // Seleccionar el texto existente para reemplazo inmediato
                if (nextInput.select) {
                    nextInput.select();
                }
            }
        },
        true // fase de captura: dispara antes que los listeners del editor Odoo
    );
});
