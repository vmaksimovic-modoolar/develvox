odoo.define('web_gantt_native.NativeGanttView', function (require) {
"use strict";

var AbstractView = require('web.BasicView');
var core = require('web.core');

var NativeGanttModel = require('web_gantt_native.NativeGanttModel');
var NativeGanttRenderer = require('web_gantt_native.NativeGanttRenderer');
var NativeGanttController = require('web_gantt_native.NativeGanttController');

var view_registry = require('web.view_registry');

var _lt = core._lt;

var GanttContainer = AbstractView.extend({

    display_name: _lt('Native Gantt'),
    icon: 'fa-tasks',

    config: {
        Model: NativeGanttModel,
        Controller: NativeGanttController,
        Renderer: NativeGanttRenderer,
    },

    init: function (viewInfo, params) {
        this._super.apply(this, arguments);

        this.loadParams.fieldsView = viewInfo;


    },
});

view_registry.add('ganttaps', GanttContainer);

return GanttContainer;

});
