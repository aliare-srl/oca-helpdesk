odoo.define("helpdesk_mgmt.tab_navigation", function (require) {
    "use strict";

    // Intercepta TAB dentro del editor HTML (campo description) para que el foco
    // salte al siguiente campo del formulario en lugar de insertar indentación.
    document.addEventListener(
        "keydown",
        function (e) {
            if (e.key !== "Tab" || e.shiftKey) return;
            var target = e.target;
            if (!target.isContentEditable) return;
            var htmlWidget = target.closest(".o_field_html");
            if (!htmlWidget) return;
            var form = htmlWidget.closest(".o_form_view");
            if (!form) return;

            e.preventDefault();
            e.stopPropagation();

            // Recopilar todos los elementos focuseables fuera del editor html
            var focusable = Array.from(
                form.querySelectorAll(
                    'input:not([disabled]):not([type="hidden"]), ' +
                    "select:not([disabled]), " +
                    "textarea:not([disabled]), " +
                    '.o_input, [tabindex]:not([tabindex="-1"])'
                )
            ).filter(function (el) {
                return !htmlWidget.contains(el) && el.offsetParent !== null;
            });

            // Buscar el primero que esté después del campo html en el DOM
            for (var i = 0; i < focusable.length; i++) {
                var pos = htmlWidget.compareDocumentPosition(focusable[i]);
                if (pos & Node.DOCUMENT_POSITION_FOLLOWING) {
                    focusable[i].focus();
                    return;
                }
            }

            // Si no hay ninguno después, enfocar el primero disponible
            if (focusable.length > 0) {
                focusable[0].focus();
            }
        },
        true // captura antes de que el editor Odoo consuma el evento
    );
});
