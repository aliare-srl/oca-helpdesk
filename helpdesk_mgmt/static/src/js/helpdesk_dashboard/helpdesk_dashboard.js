odoo.define('helpdesk_mgmt.Dashboard', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

    var PRESET_DAYS = {
        today: 0,
        '7d': 7,
        '30d': 30,
        quarter: 90,
    };

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function formatDateInput(d) {
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    }

    function statusClass(status) {
        if (status === 'green') return 'good';
        if (status === 'yellow') return 'warning';
        if (status === 'red') return 'critical';
        return '';
    }

    function statusLabel(status) {
        if (status === 'green') return 'En tiempo';
        if (status === 'yellow') return 'Próx. a vencer';
        if (status === 'red') return 'Vencido';
        return 'Sin SLA';
    }

    var HelpdeskDashboard = AbstractAction.extend({
        contentTemplate: null,
        events: {
            'click .o_hlp_dash_chip': '_onPresetClick',
            'change .o_hlp_dash_date_from': '_onDateChange',
            'change .o_hlp_dash_date_to': '_onDateChange',
            'change .o_hlp_dash_team': '_onFilterChange',
            'change .o_hlp_dash_category': '_onFilterChange',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.data = {};
            var today = new Date();
            var from = new Date();
            from.setDate(from.getDate() - PRESET_DAYS['30d']);
            this.dateFrom = formatDateInput(from);
            this.dateTo = formatDateInput(today);
            this.teamId = false;
            this.categoryId = false;
            this.teams = [];
            this.categories = [];
        },

        willStart: function () {
            var self = this;
            return Promise.all([
                this._super.apply(this, arguments),
                this._loadFilterOptions().then(function () {
                    return self._loadData();
                }),
            ]);
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._render();
            });
        },

        _loadFilterOptions: function () {
            var self = this;
            return rpc.query({
                model: 'helpdesk.ticket.team',
                method: 'search_read',
                args: [[], ['id', 'name']],
            }).then(function (teams) {
                self.teams = teams;
                return rpc.query({
                    model: 'helpdesk.ticket.category',
                    method: 'search_read',
                    args: [[], ['id', 'name']],
                });
            }).then(function (categories) {
                self.categories = categories;
            });
        },

        _rangeKwargs: function () {
            return {
                date_from: this.dateFrom ? this.dateFrom + ' 00:00:00' : false,
                date_to: this.dateTo ? this.dateTo + ' 23:59:59' : false,
            };
        },

        _loadData: function () {
            var self = this;
            var range = this._rangeKwargs();
            return rpc.query({
                model: 'helpdesk.ticket',
                method: 'get_dashboard_data',
                args: [],
                kwargs: {
                    date_from: range.date_from,
                    date_to: range.date_to,
                    team_id: this.teamId || false,
                    category_id: this.categoryId || false,
                },
            }).then(function (data) {
                self.data = data || {};
            });
        },

        _onPresetClick: function (ev) {
            var preset = $(ev.currentTarget).data('preset');
            var days = PRESET_DAYS[preset];
            if (days === undefined) {
                return;
            }
            var today = new Date();
            var from = new Date();
            if (preset !== 'today') {
                from.setDate(from.getDate() - days);
            }
            this.dateFrom = formatDateInput(from);
            this.dateTo = formatDateInput(today);
            this._reload();
        },

        _onDateChange: function () {
            var from = this.$('.o_hlp_dash_date_from').val();
            var to = this.$('.o_hlp_dash_date_to').val();
            if (!from || !to) {
                return;
            }
            this.dateFrom = from;
            this.dateTo = to;
            this._reload();
        },

        _onFilterChange: function () {
            this.teamId = this.$('.o_hlp_dash_team').val() || false;
            this.categoryId = this.$('.o_hlp_dash_category').val() || false;
            this._reload();
        },

        _reload: function () {
            var self = this;
            return this._loadData().then(function () {
                self._render();
            });
        },

        _render: function () {
            this.$el.html(QWeb.render('helpdesk_mgmt.Dashboard', this._prepareRenderData()));
        },

        _prepareRenderData: function () {
            var data = this.data || {};
            var kpis = data.kpis || {};
            var total = kpis.open_count || 0;
            var pct = function (n) {
                return total ? Math.round((n / total) * 1000) / 10 : 0;
            };
            return {
                kpis: {
                    openCount: total,
                    openPct: total ? 100 : 0,
                    green: kpis.green || 0,
                    greenPct: pct(kpis.green || 0),
                    yellow: kpis.yellow || 0,
                    yellowPct: pct(kpis.yellow || 0),
                    red: kpis.red || 0,
                    redPct: pct(kpis.red || 0),
                    avgWaitHours: kpis.avg_wait_hours || 0,
                },
                categoryTable: this._buildOpenBreakdownTable(data.category_breakdown || []),
                userTable: this._buildOpenBreakdownTable(data.user_breakdown || []),
                partnerTable: this._buildOpenBreakdownTable(data.partner_breakdown || []),
                priorityTable: this._buildOpenBreakdownTable(data.priority_breakdown || []),
                topDelayed: this._buildTopDelayed(data.top_delayed || []),
                teams: this.teams,
                categories: this.categories,
                dateFrom: this.dateFrom,
                dateTo: this.dateTo,
                teamId: this.teamId,
                categoryId: this.categoryId,
            };
        },

        _buildOpenBreakdownTable: function (rows) {
            return rows.map(function (row) {
                var riskClass = row.red > 0 ? 'critical' : (row.yellow > 0 ? 'warning' : 'good');
                return _.extend({}, row, {riskClass: riskClass});
            });
        },

        _buildTopDelayed: function (rows) {
            return rows.map(function (row) {
                return _.extend({}, row, {
                    statusClass: statusClass(row.sla_status),
                    statusLabel: statusLabel(row.sla_status),
                });
            });
        },

    });

    core.action_registry.add('helpdesk_mgmt_dashboard', HelpdeskDashboard);

    return HelpdeskDashboard;
});
