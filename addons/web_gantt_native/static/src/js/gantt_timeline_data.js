odoo.define('web_gantt_native.TimeLineData', function (require) {
"use strict";


var core = require('web.core');
var Dialog = require('web.Dialog');

var Widget = require('web.Widget');


var _t = core._t;


var GanttToolTip = require('web_gantt_native.ToolTip');
var GanttToolHint = require('web_gantt_native.ToolHint');


var GanttTimeLineData = Widget.extend({
    template: "GanttTimeLine.data",

    events: {

        'mouseover  .task-gantt-bar-plan'    :'HandleTipOver',
        'mouseout   .task-gantt-bar-plan'    :'HandleTipOut',

        // 'mousedown .task-gantt-bar-plan': 'BarClick',
    },



   // 'mouseover  .task-gantt-item, .task-gantt-timeline-row'     :'handleHoverOver',
   // 'mouseout   .task-gantt-item, .task-gantt-timeline-row'     :'handleHoverOut',

    init: function(parent, timeScale, timeType, record, options) {
        this._super(parent);
        this.parent = parent;
        this.record = record;
        this.record_id = this.record['id'];

        this.BarRecord = undefined;
        this.BarClickDiffX = undefined;
        this.BarClickX = undefined;
        this.BarClickDown = false;

        this.deadline_status = false;

        this.items_sorted = options.items_sorted;
        this.tree_view = options.tree_view;


    },

    get_position: function(gantt_date_start, gantt_date_stop, deadline_date){

        var task_start_time = gantt_date_start.getTime();
        var task_stop_time = gantt_date_stop.getTime();

        var task_start_pxscale = Math.round((task_start_time-this.parent.firstDayScale) / this.parent.pxScaleUTC);
        var task_stop_pxscale = Math.round((task_stop_time-this.parent.firstDayScale) / this.parent.pxScaleUTC);
        // var bar_width = Math.round(task_time_len / this.parent.pxScaleUTC);
        var bar_left = task_start_pxscale;
        var bar_width = task_stop_pxscale-task_start_pxscale;


        if (deadline_date) {

            var date_deadline_time = deadline_date.getTime();
            var date_deadline_pxscale = Math.round((date_deadline_time-this.parent.firstDayScale) / this.parent.pxScaleUTC);

            var bar_deadline_left = false;
            var bar_deadline_width = false;


            if (date_deadline_pxscale >= task_stop_pxscale){

                bar_deadline_left = bar_width;
                bar_deadline_width = date_deadline_pxscale-task_stop_pxscale;

                this.deadline_status = 'after_stop';

            }

            if (date_deadline_pxscale < task_stop_pxscale){

                bar_deadline_left = bar_width - (task_stop_pxscale - date_deadline_pxscale);
                bar_deadline_width = task_stop_pxscale-date_deadline_pxscale;
                this.deadline_status = 'before_stop'

            }

            if (date_deadline_pxscale <= task_start_pxscale){

                bar_deadline_left = bar_width - (task_stop_pxscale - date_deadline_pxscale);
                bar_deadline_width = task_start_pxscale-date_deadline_pxscale;
                this.deadline_status = 'before_start'

            }

        }

        return {
            bar_left: bar_left,
            bar_width: bar_width,
            bar_deadline_left : bar_deadline_left,
            bar_deadline_width : bar_deadline_width
        };

    },

    get_uposition: function(gantt_date_start, gantt_date_stop, any_date){

        var task_start_time = gantt_date_start.getTime();
        var task_stop_time = gantt_date_stop.getTime();

        var task_start_pxscale = Math.round((task_start_time-this.parent.firstDayScale) / this.parent.pxScaleUTC);
        var task_stop_pxscale = Math.round((task_stop_time-this.parent.firstDayScale) / this.parent.pxScaleUTC);

        var bar_left = task_start_pxscale;
        var bar_width = task_stop_pxscale-task_start_pxscale;

        var any_status = false;

        if (any_date) {

            var date_deadline_time = any_date.getTime();
            var date_deadline_pxscale = Math.round((date_deadline_time-this.parent.firstDayScale) / this.parent.pxScaleUTC);

            var bar_any_left = false;
            var bar_any_width = false;


            if (date_deadline_pxscale >= task_stop_pxscale){

                bar_any_left = bar_width;
                bar_any_width = date_deadline_pxscale-task_stop_pxscale;

                any_status = 'after_stop';

            }

            if (date_deadline_pxscale < task_stop_pxscale){

                bar_any_left = bar_width - (task_stop_pxscale - date_deadline_pxscale);
                bar_any_width = task_stop_pxscale-date_deadline_pxscale;
                any_status = 'before_stop'

            }

            if (date_deadline_pxscale <= task_start_pxscale){

                bar_any_left = bar_width - (task_stop_pxscale - date_deadline_pxscale);
                bar_any_width = task_start_pxscale-date_deadline_pxscale;
                any_status = 'before_start'

            }

        }

        return {
            bar_left: bar_left,
            bar_width: bar_width,
            bar_any_left : bar_any_left,
            bar_any_width : bar_any_width,
            any_status: any_status
        };

    },


    start: function(){

        var self = this;
        var id = this.record_id;


        if (!this.record.is_group) {

            //Color

            var color_gantt = false;

            if (this.record["color_gantt_set"]){

                color_gantt = this.record["color_gantt"]

            }

            //Gantt Bar

            var gantt_bar = $('<div class="task-gantt-bar-plan"></div>');

            if (this.record.schedule_mode === "auto") {
                gantt_bar = $('<div class="task-gantt-bar-plan task-gantt-bar-plan-auto"></div>');
            }

            if (this.record.constrain_type !== "asap" && this.record.constrain_type !== undefined && this.record.schedule_mode === "auto") {
                gantt_bar = $('<div class="task-gantt-bar-plan task-gantt-bar-plan-constrain"></div>');
            }


            //Possition
            var get_possition = this.get_position(this.record.task_start, this.record.task_stop, this.record.date_deadline);

            gantt_bar.css({"left": get_possition.bar_left + "px"});
            gantt_bar.css({"width": get_possition.bar_width + "px"});

            //Hiden Star End bar for change main bar
            var bar_start = $('<div class="ui-resizable-handle ui-resizable-w task-gantt-bar-plan-start"></div>');
            var bar_end = $('<div class="ui-resizable-handle ui-resizable-e task-gantt-bar-plan-end"></div>');


            if (get_possition.bar_width === 0) {
                bar_start.addClass("task-gantt-bar-plan-start-zero");
                bar_end.addClass("task-gantt-bar-plan-end-zero");
            }

            gantt_bar.append(bar_start);
            gantt_bar.append(bar_end);

            //Summary Bar : summary_date_start - summary_date_end
            // if (this.record.subtask_count > 0) {
            //
            //     var bar_summary_start = $('<div class="task-gantt-summary task-gantt-summary-start"></div>');
            //     var bar_summary_end = $('<div class="task-gantt-summary task-gantt-summary-end"></div>');
            //
            //     gantt_bar.append(bar_summary_start);
            //     gantt_bar.append(bar_summary_end);
            //
            //     var summary_width = get_possition.bar_width;
            //     var bar_summary_width = $('<div class="task-gantt-summary-width"></div>');
            //     bar_summary_width.css({"width": summary_width + "px"});
            //
            //     gantt_bar.append(bar_summary_width);
            //
            // }


            // var bar_point_start = $('<div class="task-gantt-point task-gantt-point-start"></div>');
            // var bar_point_end = $('<div class="task-gantt-point task-gantt-point-end"></div>');

            // gantt_bar.append(bar_point_start);
            // gantt_bar.append(bar_point_end);


            var done_append = true;

            if (this.parent.fields_view.arch.attrs.state_status) {
                done_append = false;
                if(this.record.state === this.parent.fields_view.arch.attrs.state_status){
                    done_append = true;
                }
            }

            if (done_append){

                var get_upossition_done = this.get_uposition(this.record.task_start, this.record.task_stop, this.record.date_done);
                var done_status = get_upossition_done.any_status;
                if (done_status){

                    var done_left = get_upossition_done.bar_any_left;
                    var done_width = get_upossition_done.bar_any_width;

                    var done_slider = $('<div class="task-gantt-done-slider fa fa-thumbs-o-up"></div>');
                    var done_slider_left = done_left+done_width;

                    if (done_status == 'before_stop' || done_status == 'before_start'){

                        done_slider_left = done_left;
                    }

                    done_slider.css({"left": done_slider_left + "px"});
                    gantt_bar.append(done_slider);


                }
            }


            //Deadline

            //Position cont

            var bar_deadline_left = get_possition.bar_deadline_left;
            var bar_deadline_width = get_possition.bar_deadline_width;


            //HTML render
            if (bar_deadline_left && bar_deadline_width){

                //Bar Deadline
                var bar_deadline = $('<div class="task-gantt-bar-deadline"></div>');

                if (this.deadline_status === 'after_stop' || this.deadline_status === 'before_start') {

                    bar_deadline.css({"left": bar_deadline_left + "px"});
                    bar_deadline.css({"width": bar_deadline_width + "px"});
                    gantt_bar.append(bar_deadline);

                }

                if (this.deadline_status === 'before_start') {

                    bar_deadline.css({"left": bar_deadline_left + "px"});
                    bar_deadline.css({"width": bar_deadline_width + "px"});
                    bar_deadline.css({"background": "rgba(255, 190, 190, 0.2)" });

                    gantt_bar.append(bar_deadline);

                }

                // var bar_deadline_overdue = $('<div class="task-gantt-bar-deadline-overdue"></div>');
                var bar_deadline_slider = $('<div class="task-gantt-deadline-slider"></div>');
                var bar_deadline_slider_left = bar_deadline_left+bar_deadline_width;

                if (this.deadline_status === 'before_stop' || this.deadline_status === 'before_start'){

                    bar_deadline_slider_left = bar_deadline_left
                }

                bar_deadline_slider.css({"left": bar_deadline_slider_left + "px"});

                // gantt_bar.append(bar_deadline_overdue);
                gantt_bar.append(bar_deadline_slider);


                this.DragDeadLine(self,id , gantt_bar, bar_deadline_slider, this.record);


            }

            //progress
            if (this.record.progress){

                // var bar_progress = $('<div class="task-gantt-progress">'+ this.record.progress +'%</div>');
                //
                // bar_progress.css({"left": get_possition.bar_width/3 + "px"});
                // gantt_bar.append(bar_progress);


                var progress_value = (get_possition.bar_width/100)*this.record.progress;

                if (progress_value < 0){

                    progress_value = -progress_value+get_possition.bar_width
                }

                var bar_progress = $('<div class="task-gantt-progress"></div>');

                bar_progress.css({"width": progress_value + "px"});

                gantt_bar.append(bar_progress);



                if (!this.record.on_gantt) {

                    var bar_progress2 = $('<div class="task-gantt-progress2">' + this.record.progress + '%</div>');
                    bar_progress2.css({"left": get_possition.bar_width / 3 + "px"});

                    if (gantt_bar.width() > 40){
                        gantt_bar.append(bar_progress2);
                    }



                }

            }


            //Milestone
            if (this.record.is_milestone) {

                bar_end.addClass("fa fa-flag fa-1x");
                gantt_bar.css({"background": "rgba(242, 197, 116, 0.1)"});


                if (this.record.schedule_mode === "auto") {
                    gantt_bar.css({"background": "rgba(111, 197, 242, 0.1)"});
                }

                if (this.record.constrain_type !== "asap" && this.record.schedule_mode === "auto") {
                    gantt_bar.css({"background": "rgba(242, 133, 113, 0.1)"});
                }

            }
            //Task Name on Gantt
            if (this.record.on_gantt) {

                var bar_name = $('<div class="task-gantt-name">'+ this.record.value_name +'</div>');

                bar_name.css({"width": get_possition.bar_width-5 + "px"});
                gantt_bar.append(bar_name);

            }

            var subtask_count = this.record['subtask_count'];
            if (subtask_count) {

                gantt_bar.css({"opacity": "0.8"});

            }


            //if exist id for data gantt
            if (id != undefined) {

                this.$el.prop('id', "task-gantt-timeline-row-" + id + "");
                this.$el.prop('data-id', id);
                this.$el.prop('allowRowHover', true);
                this.$el.prop('record', this.record);
                this.$el.prop('record_id', id);
                gantt_bar.prop('record_id', id);
                gantt_bar.prop('record', this.record);

                gantt_bar.addClass("task-gantt-bar-plan-" + id + "");

            }


            if (color_gantt){

                gantt_bar.css({"background": color_gantt});
                // gantt_bar.css({"background": color_gantt.replace(/[^,]+(?=\))/, '0.5')});
                // var yty = 787;
            }

            var critical_path = this.record['critical_path'];
            var cp_shows = this.record['cp_shows'];
            if (critical_path && cp_shows){
                gantt_bar.addClass("task-gantt-items-critical-path");
            }




            this.$el.append(gantt_bar);

        }
        else{
                var group_id = this.record.group_id[0];

                this.$el.prop('id', "task-gantt-timeline-group-row-" + group_id + "");
                this.$el.prop('group-data-id', group_id);

        }


        //Drag Actions

        //Drag Gantt Bar
        this.DragGantt(self, id, gantt_bar, this.record);
        // this.ChangeSizeEnd(self, id, bar_end, gantt_bar, this.record);
        this.ChangeSizeStart(self, id, gantt_bar, this.record);


        var fold_self = self.record['fold_self'];
        if (self.tree_view) {
            if (fold_self) {
                this.$el.css({'display': 'none'});
            }
        }





   },


    DragDeadLine: function(self, id, gantt_el, element, record) {




                 // var
                 var drag_el = element;
                 var containment_el =  "task-gantt-timeline-row-" + id + "";

                 drag_el.draggable({

                     axis: "x",
                     containment: containment_el,
                     scroll: false,

                     start: function (event, ui) {

                        self.BarRecord = record;
                        //
                        //Hint Widget Destroy
                        self.HintDestroy(self.parent);

                        //Tip Widget Destroy
                        self.TipDestroy(self.parent);

                        //Create Bar Hint
                        var gantt_line_hint = new GanttToolHint(self.parent);
                        gantt_line_hint.appendTo(self.parent.$('.task-gantt-line-hints'));

                        self.parent.hint_move_widget = gantt_line_hint;
                        //
                        // //Hide
                        self.HideDeadline("deadline");
                        self.$el.prop('allowRowHover', false);


                        // // drag_el.css({"position": "relative" });
                        // // drag_el.css({"opacity": 0.8 });
                        // // drag_el.css({"background": "rgb(76, 92, 246)" });
                        // gantt_el.css({"background": "rgba(98, 196, 51, 0.38)"});



                     },
                     drag: function (event, ui) {

                        //Hint
                        var bar_info = self.GetGanttBarPlanPxTime();
                        self.parent.hint_move_widget.show_hint(drag_el, bar_info, ui, "deadline");

                     },


                     stop: function (event, ui) {

                            //Bar Save
                            self.BarSave(self.BarRecord.id, "deadline");

                            //Hint Widget Destroy
                            self.HintDestroy(self.parent);

                            self.BarRecord = undefined;

                            drag_el.draggable('disable');




                     }

                 }).css("position", "absolute");





    },






    ChangeSizeStart: function (self, id, gantt_bar, record) {

        if (id !== undefined) {

            if (record["schedule_mode"] === "manual" || record["schedule_mode"] === undefined) {


                var containment_el = "task-gantt-timeline-row-" + id + "";

                gantt_bar.resizable({


                    handles: {
                    'e': '.task-gantt-bar-plan-end',
                    'w': '.task-gantt-bar-plan-start'

                    },


                    // containment: containment_el,
                    start: function (event, ui) {

                        self.BarRecord = event.currentTarget.record;
                        // self.BarClickDiffX = event.target.offsetLeft - event.clientX;
                        // self.BarClickX = event.clientX;
                        // self.BarClickDown = true;


                        //Hint Widget Destroy
                        self.HintDestroy(self.parent);

                        //Tip Widget Destroy
                        self.TipDestroy(self.parent);

                        //Create Bar Hint
                        var gantt_line_hint = new GanttToolHint(self.parent);
                        gantt_line_hint.appendTo(self.parent.$('.task-gantt-line-hints'));

                        self.parent.hint_move_widget = gantt_line_hint;

                        //Hide
                        self.HideDeadline();

                        self.$el.prop('allowRowHover', false);
                        // drag_el.css({"position": "relative" });
                        // drag_el.css({"opacity": 0.8 });
                        // drag_el.css({"background": "rgb(76, 92, 246)" });
                        gantt_bar.css({"background": "rgba(98, 196, 51, 0.38)"});

                    },
                    resize: function (event, ui) {

                                                //Hint
                        var bar_info = self.GetGanttBarPlanPxTime();
                        self.parent.hint_move_widget.show_hint(gantt_bar, bar_info);


                    },
                    stop: function (event, ui) {
                            //Bar Save
                            self.BarSave(self.BarRecord.id, "bar");

                            //Hint Widget Destroy
                            self.HintDestroy(self.parent);

                            self.BarRecord = undefined;
                            gantt_bar.resizable('disable');
                            gantt_bar.draggable('disable');

                            // self.$el.prop('allowRowHover', true);
                            self.ScrollToTop = $('.task-gantt').scrollTop();

                    }

                });


            }
        }

    },



    ChangeSizeEnd: function (self, id, element, gantt_bar, record) {

        if (id !== undefined) {

            if (record["schedule_mode"] === "manual" || record["schedule_mode"] === undefined) {


                                 // var
                 var drag_el = element;
                 var containment_el =  "task-gantt-timeline-row-" + id + "";

                 drag_el.draggable({

                     axis: "x",
                     containment: containment_el,
                     scroll: false,
                     zIndex: 1000,

                     start: function (event, ui) {

                        self.BarRecord = event.currentTarget.parentElement.record;
                        self.BarClickDiffX = event.target.offsetLeft - event.clientX;
                        self.BarClickX = event.clientX;

                        //Hint Widget Destroy
                        self.HintDestroy(self.parent);

                        //Tip Widget Destroy
                        self.TipDestroy(self.parent);

                        //Create Bar Hint
                        var gantt_line_hint = new GanttToolHint(self.parent);
                        gantt_line_hint.appendTo(self.parent.$('.task-gantt-line-hints'));

                        self.parent.hint_move_widget = gantt_line_hint;

                        //Hide
                        self.HideDeadline();

                        self.$el.prop('allowRowHover', false);
                        drag_el.css({"position": "relative" });
                        drag_el.css({"opacity": 0.8 });
                        drag_el.css({"background": "rgb(76, 92, 246)" });
                        gantt_bar.css({"background": "rgba(98, 196, 51, 0.38)"});


                     },
                     drag: function (event, ui) {



                        //Hint
                        var bar_info = self.GetGanttBarPlanPxTime();
                        self.parent.hint_move_widget.show_hint(gantt_bar, bar_info, ui);


                         var offsetWidth = event.target.offsetParent.offsetWidth;
                         var DiffForMove = self.BarClickX - event.clientX; //raznica mez nazatijem i tekuchej poziciji mishi
                         var BarNewPos = offsetWidth  - DiffForMove; //Velichina smechenija bloka.
                         var NewBarClickDiffX = offsetWidth - event.clientX; //tekucheje rastojanija mezdu nachalom blok i tekuchem pol mishki
                         var Kdiff =  self.BarClickDiffX - NewBarClickDiffX + 5; //Koeficent corekciji dla poderzanija rastojanije meszu nachalom
                            //bloka i tekuchem polozenijem mishi. 5 shirina elemnta end (div dragabble)

                         var new_width = BarNewPos+Kdiff+DiffForMove;

                        if (new_width > 0){
                             gantt_bar.css({"width": (new_width) + "px"});
                        }


                     },


                     stop: function (event, ui) {


                            //Bar Save
                            self.BarSave(self.BarRecord.id, "bar");

                            //Hint Widget Destroy
                            self.HintDestroy(self.parent);

                            self.BarRecord = undefined;

                            self.$el.prop('allowRowHover', true);

                            drag_el.css({"position": "absolute" });


                     }

                 }).css("position", "absolute");


            }

        }

    },



    DragGantt: function(self, id, element, record) {


        if (id !== undefined) {

            if (record["schedule_mode"] === "manual" || record["schedule_mode"] === undefined) {


                 // var
                 var drag_el = element;
                 var containment_el =  "task-gantt-timeline-row-" + id + "";

                 drag_el.draggable({

                     axis: "x",
                     containment: containment_el,
                     scroll: false,

                     start: function (event, ui) {

                        self.BarRecord = event.currentTarget.record;

                        //Hint Widget Destroy
                        self.HintDestroy(self.parent);

                        //Tip Widget Destroy
                        self.TipDestroy(self.parent);

                        //Create Bar Hint
                        var gantt_line_hint = new GanttToolHint(self.parent);
                        gantt_line_hint.appendTo(self.parent.$('.task-gantt-line-hints'));

                        self.parent.hint_move_widget = gantt_line_hint;

                        //Hide
                        self.HideDeadline();

                        self.$el.prop('allowRowHover', false);
                        // drag_el.css({"position": "relative" });
                        // drag_el.css({"opacity": 0.8 });
                        // drag_el.css({"background": "rgb(76, 92, 246)" });
                        drag_el.css({"background": "rgba(98, 196, 51, 0.38)"});



                     },
                     drag: function (event, ui) {

                        //Hint
                        var bar_info = self.GetGanttBarPlanPxTime();
                        self.parent.hint_move_widget.show_hint(drag_el, bar_info);

                     },


                     stop: function (event, ui) {

                            //Bar Save
                            self.BarSave(self.BarRecord.id, "bar");

                            //Hint Widget Destroy
                            self.HintDestroy(self.parent);

                            self.BarRecord = undefined;

                            drag_el.resizable('disable');
                            drag_el.draggable('disable');


                     }

                 }).css("position", "absolute");

            }


        }


    },


    HintDestroy: function(parent) {

        if (parent.hint_move_widget){

            parent.hint_move_widget.destroy();
            parent.hint_move_widget = undefined;
        }

    },

    TipDestroy: function(parent) {

        if (parent.tip_move_widget) {
            parent.tip_move_widget.destroy();
            parent.tip_move_widget = undefined;
        }

    },




    HandleTipOver: function(event) {

        var self = this;

        // var bar_record_id = event.target.record_id ;
        // var bar_record_id = this.record_id;
        // var gantt_bar = $(".task-gantt-bar-plan-" + bar_record_id + "");

        if (self.parent.tip_move_widget) {
            self.parent.tip_move_widget.destroy();
            self.parent.tip_move_widget = undefined;

        }

         if (!self.parent.hint_move_widget) {

             var gantt_bar = this.$el.children('.task-gantt-bar-plan');
            // //Create Bar Hint
            var gantt_line_tip = new GanttToolTip(self.parent, gantt_bar);
            gantt_line_tip.appendTo(self.parent.$('.task-gantt-line-tips'));
            self.parent.tip_move_widget = gantt_line_tip;

         }

    },


    HandleTipOut: function() {

        var self = this;

        if (self.parent.tip_move_widget) {
            self.parent.tip_move_widget.destroy();
            self.parent.tip_move_widget = undefined;
        }

    },



    HideDeadline: function(type){

        var gantt_bar = this.$el.children('.task-gantt-bar-plan');



        if (type==="deadline"){

            //Deadline
            var gantt_bardeadline = gantt_bar.children('.task-gantt-bar-deadline');
            if (gantt_bardeadline) {
                gantt_bardeadline.hide();
            }


        }
        else{
            //Deadline
            var gantt_bardeadline = gantt_bar.children('.task-gantt-bar-deadline');
            if (gantt_bardeadline) {
                gantt_bardeadline.hide();
            }

            //Done Slider
            var gantt_done_slider = gantt_bar.children('.task-gantt-done-slider');
            if (gantt_done_slider) {
                gantt_done_slider.hide();
            }


            //Deadline Slider
            var bar_deadline_slider = gantt_bar.children('.task-gantt-deadline-slider');

            if (bar_deadline_slider) {
                bar_deadline_slider.hide();
            }

        }



    },


//Save BAR

    CheckReadonly: function(fields){
        var self = this;

        var readonly_fields = [];
        _.each(fields, function (field, field_key ) {

            var readonly_status  = false;
            var check_field = self.parent.fields[field];
            var check_state = self.BarRecord["state"];
            var states = check_field["states"];

            if (check_state && states ){

                var where_state = [];

                _.each(states, function (state, key) {

                    var param1 = false;
                    var param2 = false;

                    if (state[0].length === 2){

                        param1 = state[0][0];
                        param2 = state[0][1];
                    }

                    if (param1 === 'readonly'){
                       where_state.push({state : key, param: param2 });
                    }

                    if (param2 === true){
                        readonly_status = true
                    }

                });

                var check_readonly = _.findWhere(where_state,{state: check_state});

                if (readonly_status){
                    if (!check_readonly){
                        readonly_status = false
                    }
                }
                else{
                    if (!check_readonly){
                        readonly_status = true
                    }
                }
            }
            else{

                readonly_status = check_field.readonly

            }

         readonly_fields.push({field : field, readonly: readonly_status });

        });
        return readonly_fields;

    },



    BarSave: function(r_id, type){

        var self = this ;
        var data = {};

        var bar_info = this.GetGanttBarPlanPxTime();

        var model_fields_dict = this.parent.model_fields_dict;
        var parent = this.parent;

        if (type === "bar"){

            var f_data_start = model_fields_dict["date_start"];
            var f_date_stop = model_fields_dict["date_stop"];

            data[f_data_start] = bar_info.task_start;
            data[f_date_stop] = bar_info.task_end;

            this.parent.TimeToLeft = $('.task-gantt-timeline').scrollLeft();
            this.parent.ScrollToTop = $('.task-gantt').scrollTop();

            // Redonly Check

            var check_filed = [f_data_start, f_date_stop];
            var readonly = this.CheckReadonly(check_filed);

            var check_readonly = _.findWhere(readonly,{readonly: true});

            if (check_readonly){
                Dialog.alert(this, _.str.sprintf(_t("You are trying to write on a read-only field! : '%s' "),check_readonly["field"]));

                return self.trigger_up('gantt_refresh_after_change');
            }

        }


        if (type === "deadline"){


            var f_date_deadline = model_fields_dict["date_deadline"];


            data[f_date_deadline] = bar_info.deadline_time;


            this.parent.TimeToLeft = $('.task-gantt-timeline').scrollLeft();
            this.parent.ScrollToTop = $('.task-gantt').scrollTop();

            // Redonly Check

            var check_filed_deadline = [f_date_deadline];
            var readonly_deadline = this.CheckReadonly(check_filed_deadline);

            var check_readonly_deadline = _.findWhere(readonly_deadline,{readonly: true});


            if (check_readonly_deadline){
                Dialog.alert(this, _.str.sprintf(_t("You are trying to write on a read-only field! : '%s' "),check_readonly_deadline["field"]));

                return self.trigger_up('gantt_refresh_after_change');
            }



        }



        //Save and refresh after change
        parent._rpc({
                model: parent.state.modelName,
                method: 'write',
                args: [[r_id], data],
                context: parent.state.contexts
            })
            .then(function(ev) {
                self.trigger_up('gantt_refresh_after_change',ev );
        });

    },



     GetGanttBarPlanPxTime: function (){

        var gantt_bar = this.$el.children('.task-gantt-bar-plan');

        var tleft = parseInt(gantt_bar.css('left'), 10);
        var twidth = parseInt(gantt_bar.css('width'), 10);

        var tright = tleft + twidth;
        var task_start = (tleft*this.parent.pxScaleUTC)+this.parent.firstDayScale;
        var task_end = (tright*this.parent.pxScaleUTC)+this.parent.firstDayScale;


        var new_task_start = new Date(0); // The 0 there is the key, which sets the date to the epoch setUTCSeconds(task_start);
        new_task_start.setTime(task_start);

        var new_task_end = new Date(0); // The 0 there is the key, which sets the date to the epoch setUTCSeconds(task_start);
        new_task_end.setTime(task_end);

        var deadline_time = false;

        var gantt_bar_deadline = gantt_bar.children('.task-gantt-deadline-slider');

        if (gantt_bar_deadline) {

            // var deadline_left = parseInt(gantt_bar_deadline.css('left'), 10);
            // var deadline_width = parseInt(gantt_bar_deadline.css('width'), 10);
            //var deadline_px = deadline_left + deadline_width;
            // var deadline_px = parseInt(gantt_bar_deadline.css('left'), 10);

            // var deadline_left = parseInt(gantt_bar_deadline.css('left'), 10);

            var deadline_px1 = parseInt(gantt_bar_deadline.css('left'), 10);

            var deadline_px = deadline_px1 + tleft;

            if (deadline_px1 < 0) {

                deadline_px = tleft + deadline_px1;
            }


            deadline_time = (deadline_px*this.parent.pxScaleUTC)+this.parent.firstDayScale;

            var new_deadline_time = new Date(0); // The 0 there is the key, which sets the date to the epoch setUTCSeconds(task_start);
            new_deadline_time.setTime(deadline_time);

            var test = 45;




        }


        return {
            task_start: new_task_start,
            task_end:new_task_end,
            deadline_time : new_deadline_time

        };

     }



});

return GanttTimeLineData;

});