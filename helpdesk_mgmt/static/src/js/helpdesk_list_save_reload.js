odoo.define('helpdesk_mgmt.list_save_reload', function (require) {
    'use strict';
    var ListController = require('web.ListController');
    ListController.include({
        _helpdeskIsHelpdeskView: function () {
            var byClass = this.$el && this.$el.find('table.o_helpdesk_aliare').length > 0;
            var byModel = this.modelName === 'helpdesk.ticket';
            return byClass || byModel;
        },
        _confirmSave: function (id, options) {
            var self = this;
            var result = this._super.apply(this, arguments);
            if (!this._helpdeskIsHelpdeskView()) {
                return result;
            }
            return Promise.resolve(result).then(function () {
                return self.reload();
            }).catch(function (err) {
                console.error('[helpdesk_mgmt] Error al recargar la grilla:', err);
            });
        },
    });
    return ListController;
});
