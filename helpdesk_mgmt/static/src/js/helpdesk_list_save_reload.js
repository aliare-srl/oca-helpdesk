/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

patch(ListController.prototype, "helpdesk_mgmt.list_save_reload", {
    async onClickSave() {
        const isHelpdeskView =
            this.rootRef.el &&
            this.rootRef.el.querySelector("table.o_helpdesk_aliare");

        if (!isHelpdeskView) {
            return this._super(...arguments);
        }

        const editedRecord = this.model.root.editedRecord;
        if (!editedRecord) return;

        const saved = await editedRecord.save();
        if (saved) {
            await this.model.root.load();
            this.model.notify();
        }
    },
});
