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

    function formatDateInput(d) {
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
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

    function truncateLabel(name, maxChars) {
        if (!name) return '';
        if (name.length <= maxChars) return name;
        return name.slice(0, maxChars - 1) + '…';
    }

    var HelpdeskDashboard = AbstractAction.extend({
        contentTemplate: null,
        events: {
            'click .o_hlp_dash_chip': '_onPresetClick',
            'change .o_hlp_dash_date_from': '_onDateChange',
            'change .o_hlp_dash_date_to': '_onDateChange',
            'change .o_hlp_dash_team': '_onFilterChange',
            'change .o_hlp_dash_category': '_onFilterChange',
            'click .o_hlp_dash_trend_toggle': '_onTrendToggle',
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
            if (preset === 'today') {
                // from = today
            } else {
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
                categoryStackedBars: this._buildStackedBars(data.category_breakdown || []),
                categoryTable: this._buildBreakdownTable(data.category_breakdown || []),
                userTable: this._buildBreakdownTable(data.user_breakdown || []),
                categoryBars: this._buildVerticalBars(data.category_volume || [], CATEGORY_COLORS),
                priorityBars: this._buildVerticalBars(data.priority_volume || [], PRIORITY_COLORS),
                teams: this.teams,
                categories: this.categories,
                dateFrom: this.dateFrom,
                dateTo: this.dateTo,
                teamId: this.teamId,
                categoryId: this.categoryId,
            };
        },

        _buildBreakdownTable: function (rows) {
            return rows.map(function (row) {
                return _.extend({}, row, {complianceClass: slaStatusClass(row.compliance_pct)});
            });
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
                var y = yBottom - f * (yBottom - yTop);
                return {
                    y: y.toFixed(1),
                    labelY: (y + 4).toFixed(1),
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

        _buildStackedBars: function (rows) {
            if (!rows.length) {
                return {hasData: false};
            }
            var maxTotal = 0;
            rows.forEach(function (r) {
                maxTotal = Math.max(maxTotal, r.green + r.yellow + r.red);
            });
            var xStart = 150, trackWidth = 250, rowH = 32;
            var bars = rows.map(function (r, i) {
                var withSla = r.green + r.yellow + r.red;
                var barWidth = maxTotal ? (withSla / maxTotal) * trackWidth : 0;
                var y = 10 + i * rowH;
                var segments = [];
                var cursor = xStart;
                [
                    ['good', r.green],
                    ['warning', r.yellow],
                    ['critical', r.red],
                ].forEach(function (pair) {
                    var segWidth = withSla ? (pair[1] / withSla) * barWidth : 0;
                    if (segWidth > 0.5) {
                        segments.push({
                            x: cursor.toFixed(1),
                            width: segWidth.toFixed(1),
                            statusClass: pair[0],
                        });
                    }
                    cursor += segWidth;
                });
                return {
                    name: r.name,
                    nameShort: truncateLabel(r.name, 20),
                    total: withSla,
                    segments: segments,
                    y: y,
                    labelY: (y + 12).toFixed(1),
                    totalLabelX: (xStart + barWidth + 10).toFixed(1),
                };
            });
            return {
                bars: bars,
                hasData: true,
                height: 10 + rows.length * rowH + 10,
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
                var y = baseline - h;
                return {
                    name: r.name,
                    nameShort: truncateLabel(r.name, 9),
                    count: r.count,
                    x: x,
                    width: barWidth,
                    y: y.toFixed(1),
                    labelY: (y - 6).toFixed(1),
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
