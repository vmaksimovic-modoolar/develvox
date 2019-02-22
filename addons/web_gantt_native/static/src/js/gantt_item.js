odoo.define('web_gantt_native.Item', function (require) {
"use strict";


var core = require('web.core');
// var form_common = require('web.form_common');
var dialogs = require('web.view_dialogs');

var Widget = require('web.Widget');
var Model = require('web.AbstractModel');

var framework = require('web.framework');

var _lt = core._lt;
var _t = core._t;



var GanttListItem = Widget.extend({
    template: "GanttList.item",

    custom_events: {
        'item_export_wizard': 'open_export_wizard',
        'item_record_edit': 'edit_record',
        'item_record_add':  'add_record',
        'focus_gantt_line' : 'focus_gantt_line',
        'item_plan_action' : 'plan_action',
        'item_fold' : 'fold_action',
        // 'critical_path' : 'critical_path_action'

    },

    init: function(parent, record, options) {

        this._super(parent);
        this.record = record;
        this.items_sorted = options.items_sorted;
        this.export_wizard = options.export_wizard;
        this.main_group_id_name = options.main_group_id_name;
        this.action_menu = options.action_menu;
        this.tree_view = options.tree_view;


    },

    start: function() {

        var self = this;
        var name = self.record['value_name'];

        var level = self.record['level'];
        var subtask_count = self.record['subtask_count'];

        // if (this.items_sorted){
        //     level = self.record['sorting_level'];
        // }

        if (this.tree_view){
            var sorting_level = self.record['sorting_level'];

             if (sorting_level)
             {
                 level = level + sorting_level;
             }
        }

        var id = self.record['id'];
        var project_id = self.record['project_id'];

        var fold_self = self.record['fold_self'];
        var fold_group = self.record['fold_group'];
        var fold_child = self.record['fold_child'];


        var padding = 28; //68
        var padding_depth = 15;
        var padding_default = 20;
        var css_style_padding_left = 0;

        // if (!this.record.is_group && self.items_sorted) {
        //     css_style_padding_left = padding;
        // }

        if (!this.record.is_group && self.tree_view) {
            css_style_padding_left = padding;
        }
        else{
            this.$el.toggleClass('ui-state-disabled-group');
            css_style_padding_left = padding_default;
        }


        if (level > 0) {
            var padlevel = padding;
            var paddepth = padding_depth * (level);
            css_style_padding_left = padlevel + paddepth;
        }

        this.$el.css({'padding-left': css_style_padding_left + "px"});

        // if (self.items_sorted) {
        //     if (fold_self) {
        //         this.$el.css({'display': 'none'});
        //     }
        // }

        if (self.tree_view) {
            if (fold_self) {
                this.$el.css({'display': 'none'});
            }
        }


        this.$el.prop('sorting', true);

        if (id != undefined) {
            this.$el.prop('id', "task-gantt-item-" + id + "");
            this.$el.prop('data-id', id);
            this.$el.prop('allowRowHover', true);
        }

        if (!this.record.is_group) {
            this.$el.append('<span class="task-gantt-focus"><i class="fa fa-crosshairs fa-1x"></i></span>');
        }

        if (this.record.is_group) {

            this.$el.css({'background-color':  "rgba(40, 95, 143, 0.10)"});


        }

        if (this.record.is_group && level === 0) {

            this.$el.css({'background-color':  "beige"});

        }




        this.$el.append('<span class="task-gantt-item-handle"></span>');

        if (this.record.is_group) {

            if (fold_group){
                this.$el.append('<span class="task-gantt-caret-right"><i class="fa fa-caret-right"></i></span>');

                name =  "("+self.record["task_count"] +") - " + name;

            }
            else{
                this.$el.append('<span class="task-gantt-caret-right"><i class="fa fa-caret-down"></i></span>');
            }

            this.$el.append('<span class="task-gantt-item-name task-gantt-items-group">'+name+'</span>');

            if (this.record.group_field === self.action_menu){

                var first_bar = $('<div class="task-gantt-item-info" style="float: right;"/>');



                 // this.$el.append('<div class="task-gantt-item-info" style="float: right;">'+duration_humanize+'</div>');

                first_bar.append('<span class="task-gantt-plus"><i class="fa fa-plus fa-1x"></i></span>');
                first_bar.append('<span class="task-gantt-refresh"><i class="fa fa-refresh fa-1x"></i></span>');
                if (self.export_wizard){
                    first_bar.append('<span class="task-gantt-wizard"><i class="fa fa-arrow-right fa-arrow-click fa-1x"></i></span>');
                }
                // first_bar.append('<span class="task-gantt-critical"><i class="fa fa-line-chart fa-1x"></i></span>');
                this.$el.append(first_bar);
            }

            // this.$el.append('<div class="task-gantt-item-info" style="float: right;">'+duration_humanize+'</div>');



        }
        else{

            // if (subtask_count && this.items_sorted){
            if (subtask_count && this.tree_view){

                    if (fold_child){

                        this.$el.append('<span class="task-gantt-caret-right"><i class="fa fa-plus-square-o"></i></span>');
                        name =  "("+self.record["subtask_count"] +") - " + name;

                    }
                    else{
                        this.$el.append('<span class="task-gantt-caret-right"><i class="fa fa-minus-square-o"></i></span>');
                    }

                    this.$el.append('<span class="task-gantt-item-name task-gantt-items-subtask">'+name+'</span>');
                }
                else{
                    if (this.record.plan_action) {
                        this.$el.append('<i class="fa fa-exclamation"></i>');
                    }
                    this.$el.append('<span class="task-gantt-item-name">'+name+'</span>');
                }


            var duration = self.record['duration'];
            var duration_units = undefined;

            if (duration){

                var duration_scale = self.record['duration_scale'];

                if (duration_scale) {

                    duration_units =  duration_scale.split(",");

                }
                // Array of strings to define which units are used to display the duration (if needed).
                // Can be one, or a combination of any, of the following:
                // ['y', 'mo', 'w', 'd', 'h', 'm', 's', 'ms']
                //
                // humanizeDuration(3600000, { units: ['h'] })       // '1 hour'
                // humanizeDuration(3600000, { units: ['m'] })       // '60 minutes'
                // humanizeDuration(3600000, { units: ['d', 'h'] })  // '1 hour'

                var duration_humanize = humanizeDuration(duration*1000, { round: true });
                if (duration_units){
                    duration_humanize = humanizeDuration(duration*1000,{ units: duration_units, round: true });
                    //duration_humanize = humanizeDuration(duration*1000,{ units: duration_units});
                }


                if (subtask_count){
                    this.$el.append('<div class="task-gantt-item-info task-gantt-items-subtask" style="float: right;">'+duration_humanize+'</div>');
                }
                else{
                    this.$el.append('<div class="task-gantt-item-info" style="float: right;">'+duration_humanize+'</div>');
                }

            }


        }


    },



    renderElement: function () {
        this._super();

        this.$el.data('record', this);
        this.$el.on('click', this.proxy('on_global_click'));

    },

    open_export_wizard: function(event){

        var test = 45;

        var context = this.__parentedParent.state.contexts;
        var self = this.__parentedParent;

        var group_id = event.data["group_id"];

        context['default_group_id'] = group_id || false;

        var res_model = event.data["exoprt_wizard"];

        var pop = new dialogs.FormViewDialog(this.__parentedParent, {
            res_model: res_model,
            res_id: false,
            context: context,
            title: _t("PDF Report for Project"),
        }).open();

    },


    new_record: function(default_project_id){

        var context = this.__parentedParent.state.contexts;
        var self = this.__parentedParent;
        context['default_project_id'] = default_project_id || false;

        var pop = new dialogs.FormViewDialog(this.__parentedParent, {
            res_model: 'project.task',
            res_id: false,
            context: context,
            title: _t("Please Select Project Firt For Task"),
            on_saved: function () {
                self.trigger_up('gantt_refresh_after_change' )
                },
        }).open();

    },

    plan_action: function(event) {

        if (event.data.is_group && event.data.group_field === 'project_id') {
            var self = this.__parentedParent;
            var  res_id = event.data.group_id;
            var  res_model = 'project.task';
            framework.blockUI();

            self._rpc({
                    model: res_model,
                    method: 'scheduler_plan',
                    args: [res_id],
                    context: self.state.contexts
                })
                .then(function(ev) {
                    framework.unblockUI();
                    self.trigger_up('gantt_refresh_after_change',ev );
            });
        }
    },


    // critical_path_action: function(event) {
    //
    //     if (event.data.is_group && event.data.group_field === 'project_id') {
    //         var self = this.__parentedParent;
    //         var  res_id = event.data.group_id;
    //         var  res_model = 'project.task';
    //         framework.blockUI();
    //
    //         self._rpc({
    //                 model: res_model,
    //                 method: 'critical_path_hide',
    //                 args: [res_id],
    //                 context: self.state.contexts
    //             })
    //             .then(function(ev) {
    //                 framework.unblockUI();
    //                 self.trigger_up('gantt_refresh_after_change',ev );
    //         });
    //     }
    // },


    fold_action: function(event) {

     //   if (event.data.is_group && event.data.group_field == 'project_id') {
            var self = this.__parentedParent;
            var  res_id = event.data.id;
            var  res_model = 'project.task';


            if (event.data.is_group && event.data.group_field === 'project_id'){
                res_id = event.data.group_id;
                res_model = 'project.project';
            }

            framework.blockUI();
            self._rpc({
                    model: res_model,
                    method: 'fold',
                    args: [res_id],
                    context: self.state.contexts
                })
                .then(function(ev) {
                    framework.unblockUI();
                    self.trigger_up('gantt_refresh_after_change',ev );
            });
       // }
    },



    add_record: function(event) {

        this.new_record(event.data.group_id);
    },

    open_record: function (event, options) {


        var res_id = false;
        var res_model = false;
        var res_open = false;
        var start_date = false;

        var readonly = false;

        var buttons = [
                {
                    text: _lt("Save"),
                    classes: 'btn-primary',
                    close: true,
                    click:  function () {
                        this._save().then(
                            self.trigger_up('gantt_refresh_after_change' )
                        );
                    }
                },

                {
                    text: _t("Edit in Form View"),
                    classes: 'btn-primary',
                    close: true,
                    click: function() {

                        this.trigger_up('open_record', {res_id: this.res_id, mode: "edit", model : this.res_model});
                    }},

                {
                    text: _lt("Delete"),
                    classes: 'btn-default',
                    close: true,
                    click: function () {

                        self._rpc({
                                model: this.res_model,
                                method: 'unlink',
                                args: [this.res_id],
                            })
                            .then(function(ev) {
                                self.trigger_up('gantt_refresh_after_change',ev );
                        });

                }},

                {
                    text: _lt("Close"),
                    classes: 'btn-default',
                    close: true,
                    click: function (){
                        self.trigger_up('gantt_refresh_after_change' )
                    }}
            ];



        if (event.data.is_group && event.data.group_field == 'project_id') {

            res_id = event.data.group_id;
            res_model = 'project.project';
            res_open = true;
            readonly = false;
            buttons.splice(1, 1)

        }

         if ( event.data.is_group == false && event.data.id ) {

            res_id = event.data.id;
            res_model = this.__parentedParent.state.modelName;
            res_open = true;

        }


        if (res_open) {

            var self = this.__parentedParent;

            var rowdata = '#task-gantt-timeline-row-'+res_id;
            var rowitem = '#task-gantt-item-'+res_id;

            $(rowdata).addClass("task-gantt-timeline-row-hover");
            $(rowitem).addClass("task-gantt-item-hover");

            self.hover_id = res_id;

            self.TimeToLeft = $('.task-gantt-timeline').scrollLeft();
            self.ScrollToTop = $('.task-gantt').scrollTop();


            var view_id = false;

            this.model = res_model;

            new dialogs.FormViewDialog(this.__parentedParent, {

                res_model: res_model,
                res_id: res_id,
                view_id: view_id,
                context: this.__parentedParent.state.contexts,
                readonly: readonly,
                buttons: buttons,

            }).open();


        } else {
            this.__parentedParent.do_warn("Gannt: Open Only - Project or Task # " + event.data.id);
        }
    },

    edit_record: function (event) {
        this.open_record(event, {mode: 'edit'});
    },




    focus_gantt_line: function (event) {

        var self = this.__parentedParent.__parentedParent;

        var toscale = Math.round((event.target.record.task_start.getTime()-self.renderer.firstDayScale) / self.renderer.pxScaleUTC);
        self.renderer.TimeToLeft = toscale;

        var new_toscale = toscale-500;
        if (new_toscale < 0){
            new_toscale = 0;
        }


        $('.timeline-gantt-head').animate( { scrollLeft: new_toscale }, 1000);
        $('.task-gantt-timeline').animate( { scrollLeft: new_toscale }, 1000);
        self.renderer.gantt_timeline_scroll_widget.scrollOffset(new_toscale);



    },


    on_global_click: function (ev) {

        if (!ev.isTrigger) { //human detect
            var trigger = true;

            if (trigger) {
                var is_group = this.record.is_group || false;
                var group_id = false;
                var group_field = false;


                var start_date = this.record.task_start;

                if (typeof start_date !== typeof undefined && start_date !== false) {
                   start_date =  start_date.getTime()
                }

                //Fold
                // if (this.items_sorted){
                if (this.tree_view){

                    if ( $(ev.target).hasClass("fa-caret-right") || $(ev.target).hasClass("fa-caret-down")
                    || $(ev.target).hasClass("fa-plus-square-o") || $(ev.target).hasClass("fa-minus-square-o")

                    ) {

                        if (is_group) {
                            group_id = this.record.group_id[0];
                            group_field = this.record.group_field;
                        }

                       this.trigger_up('item_fold', {
                           id: this.record.id,
                           is_group: is_group,
                           group_id: group_id,
                           group_field: group_field,
                           start_date: start_date
                       });
                    }

                }





                //Edit Task
                if ($(ev.target).hasClass("task-gantt-item-name" )) {

                    if (is_group) {

                        group_id = this.record.group_id[0];
                        group_field = this.record.group_field;
                    }

                   this.trigger_up('item_record_edit', {
                       id: this.record.id,
                       is_group: is_group,
                       group_id: group_id,
                       group_field: group_field,
                       start_date: start_date

                   });

                }
                //Wizard
                if ($(ev.target).hasClass("fa-arrow-click" )) {

                    if (is_group) {

                        group_id = this.record.group_id[0];
                        group_field = this.record.group_field;
                    }

                   this.trigger_up('item_export_wizard', {
                       id: this.record.id,
                       is_group: is_group,
                       group_id: group_id,
                       group_field: group_field,
                       exoprt_wizard: this.export_wizard
                   });

                }
                //New Task
                if ($(ev.target).hasClass("fa-plus")) {

                    if (is_group) {
                        group_id = this.record.group_id[0];
                        group_field = this.record.group_field;
                    }

                    this.trigger_up('item_record_add', {
                        id: this.record.id,
                        is_group: is_group,
                        group_id: group_id,
                        group_field: group_field,
                        start_date: start_date
                    });
                }
                //Scheduling action
                if ($(ev.target).hasClass("fa-refresh")) {

                    if (is_group) {
                        group_id = this.record.group_id[0];
                        group_field = this.record.group_field;
                    }

                    this.trigger_up('item_plan_action', {
                        id: this.record.id,
                        is_group: is_group,
                        group_id: group_id,
                        group_field: group_field,
                        start_date: start_date
                    });
                }

                // //Critical path action
                // if ($(ev.target).hasClass("fa-line-chart")) {
                //
                //     if (is_group) {
                //         group_id = this.record.group_id[0];
                //         group_field = this.record.group_field;
                //     }
                //
                //     this.trigger_up('critical_path', {
                //         id: this.record.id,
                //         is_group: is_group,
                //         group_id: group_id,
                //         group_field: group_field,
                //         start_date: start_date
                //     });
                // }




                //Focus Task
                if ($(ev.target).hasClass("fa-crosshairs")) {
                   this.trigger_up('focus_gantt_line', {id: this.record.id});
                }



            }
        }
    },



});

return GanttListItem;

});