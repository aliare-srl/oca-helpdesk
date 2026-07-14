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

    var CATEGORY_COLORS = [
        'var(--hlp-series-1)', 'var(--hlp-series-2)', 'var(--hlp-series-3)',
        'var(--hlp-series-4)', 'var(--hlp-series-5)', 'var(--hlp-series-8)',
    ];
    var PRIORITY_COLORS = [
        'var(--hlp-seq-250)', 'var(--hlp-seq-350)', 'var(--hlp-seq-450)', 'var(--hlp-seq-550)',
    ];

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function formatDateTime(d) {
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
            + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    }

    function formatWeekLabel(isoDate) {
        if (!isoDate) return '';
        var parts = isoDate.split('-');
        if (parts.length !== 3) return isoDate;
        return parts[2] + '/' + parts[1];
    }

    function slaStatusClass(pct) {
        if (pct >= 90) return 'good';
        if (pct >= 75) return 'warning';
        return 'critical';
    }

    var HelpdeskDashboard = AbstractAction.extend({
        contentTemplate: null,
        events: {
            'click .o_hlp_dash_chip': '_onPresetClick',
            'change .o_hlp_dash_team': '_onFilterChange',
            'change .o_hlp_dash_category': '_onFilterChange',
            'click .o_hlp_dash_trend_toggle': '_onTrendToggle',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.data = {};
            this.preset = '30d';
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

        _dateRange: function () {
            var days = PRESET_DAYS[this.preset];
            var to = new Date();
            var from = new Date();
            if (this.preset === 'today') {
                from.setHours(0, 0, 0, 0);
            } else {
                from.setDate(from.getDate() - days);
            }
            return {
                date_from: formatDateTime(from),
                date_to: formatDateTime(to),
            };
        },

        _loadData: function () {
            var self = this;
            var range = this._dateRange();
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
            if (!preset || preset === this.preset) {
                return;
            }
            this.preset = preset;
            this._reload();
        },

        _onFilterChange: function () {
            this.teamId = this.$('.o_hlp_dash_team').val() || false;
            this.categoryId = this.$('.o_hlp_dash_category').val() || false;
            this._reload();
        },

        _onTrendToggle: function () {
            this.$('.o_hlp_dash_trend_svg').toggleClass('d-none');
            this.$('.o_hlp_dash_trend_table').toggleClass('d-none');
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
            var kpisPrev = data.kpis_prev || {};
            return {
                kpis: this._buildKpiTiles(kpis, kpisPrev),
                trend: this._buildTrend(data.trend || []),
                slaByTeam: this._buildSlaBars(data.sla_by_team || []),
                categoryBars: this._buildVerticalBars(data.category_volume || [], CATEGORY_COLORS),
                priorityBars: this._buildVerticalBars(data.priority_volume || [], PRIORITY_COLORS),
                teamTable: (data.team_table || []).map(function (row) {
                    return _.extend({}, row, {complianceClass: slaStatusClass(row.compliance_pct)});
                }),
                teams: this.teams,
                categories: this.categories,
                preset: this.preset,
                teamId: this.teamId,
                categoryId: this.categoryId,
            };
        },

        _buildKpiTiles: function (kpis, prev) {
            function delta(key, lowerIsBetter) {
                if (!(key in prev)) {
                    return null;
                }
                var diff = Math.round((kpis[key] - prev[key]) * 10) / 10;
                if (diff === 0) {
                    return {label: 'Sin cambios vs. período anterior', good: true};
                }
                var good = lowerIsBetter ? diff < 0 : diff > 0;
                var arrow = diff > 0 ? '▲' : '▼';
                return {
                    label: arrow + ' ' + Math.abs(diff) + ' vs. período anterior',
                    good: good,
                };
            }
            return {
                slaCompliance: kpis.sla_compliance_pct || 0,
                slaComplianceDelta: delta('sla_compliance_pct', false),
                overdueNow: kpis.overdue_now || 0,
                avgResolution: kpis.avg_resolution_hours || 0,
                avgResolutionDelta: delta('avg_resolution_hours', true),
                avgAssignment: kpis.avg_assignment_hours || 0,
                avgAssignmentDelta: delta('avg_assignment_hours', true),
                openCount: kpis.open_count || 0,
            };
        },

        _buildTrend: function (rows) {
            if (!rows.length) {
                return {hasData: false};
            }
            var maxVal = 1;
            rows.forEach(function (r) {
                maxVal = Math.max(maxVal, r.created, r.closed);
            });
            var top = Math.ceil(maxVal / 5) * 5 || 5;
            var xStart = 40, xEnd = 580, yTop = 20, yBottom = 200;
            var n = rows.length;
            var stepX = n > 1 ? (xEnd - xStart) / (n - 1) : 0;
            var scaleY = function (v) {
                return (yBottom - (v / top) * (yBottom - yTop)).toFixed(1);
            };
            var createdPts = [];
            var closedPts = [];
            var xLabels = [];
            rows.forEach(function (r, i) {
                var x = (xStart + stepX * i).toFixed(1);
                createdPts.push(x + ',' + scaleY(r.created));
                closedPts.push(x + ',' + scaleY(r.closed));
                xLabels.push({x: x, label: formatWeekLabel(r.week)});
            });
            var gridLines = [0.25, 0.5, 0.75, 1].map(function (f) {
                return {
                    y: (yBottom - f * (yBottom - yTop)).toFixed(1),
                    value: Math.round(top * f),
                };
            });
            var last = rows[rows.length - 1];
            return {
                hasData: true,
                createdPoints: createdPts.join(' '),
                closedPoints: closedPts.join(' '),
                xLabels: xLabels,
                gridLines: gridLines,
                lastX: (xStart + stepX * (n - 1)).toFixed(1),
                lastCreatedY: scaleY(last.created),
                lastClosedY: scaleY(last.closed),
                lastCreated: last.created,
                lastClosed: last.closed,
                rows: rows,
            };
        },

        _buildSlaBars: function (rows) {
            var xStart = 140, maxWidth = 260, rowH = 32;
            var bars = rows.map(function (r, i) {
                var pct = r.compliance_pct;
                return {
                    name: r.team_name,
                    pct: pct,
                    width: (pct / 100 * maxWidth).toFixed(1),
                    y: 10 + i * rowH,
                    statusClass: slaStatusClass(pct),
                };
            });
            return {
                bars: bars,
                hasData: bars.length > 0,
                height: bars.length ? 10 + bars.length * rowH + 10 : 40,
                xStart: xStart,
            };
        },

        _buildVerticalBars: function (rows, colorSlots) {
            if (!rows.length) {
                return {hasData: false};
            }
            var maxVal = 0;
            rows.forEach(function (r) {
                maxVal = Math.max(maxVal, r.count);
            });
            var chartTop = 20, baseline = 160, barWidth = 42, gap = 20, xStart = 30;
            var bars = rows.map(function (r, i) {
                var h = maxVal ? (r.count / maxVal) * (baseline - chartTop) : 0;
                var x = xStart + i * (barWidth + gap);
                return {
                    name: r.name,
                    count: r.count,
                    x: x,
                    width: barWidth,
                    y: (baseline - h).toFixed(1),
                    height: Math.max(h, 1).toFixed(1),
                    color: colorSlots[i % colorSlots.length],
                    centerX: x + barWidth / 2,
                };
            });
            return {
                hasData: true,
                bars: bars,
                width: xStart + rows.length * (barWidth + gap) + 20,
                baseline: baseline,
            };
        },
    });

    core.action_registry.add('helpdesk_mgmt_dashboard', HelpdeskDashboard);

    return HelpdeskDashboard;
});
