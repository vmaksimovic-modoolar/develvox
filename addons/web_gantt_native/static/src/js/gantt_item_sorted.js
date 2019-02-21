odoo.define('web_gantt_native.Item_sorted', function (require) {
"use strict";

var Widget = require('web.Widget');
var Model = require('web.AbstractModel');
var framework = require('web.framework');

var GanttListSortingItem = Widget.extend({
    template: "GanttList.sorting.item",

    init: function (parent, record, options) {

        this.parent = parent;
        this._super(parent);
        this.record = record;
        this.items_sorted = options.items_sorted;

    },
    start: function () {
        var self = this;
        var id = self.record['id'];
        var name = self.record['value_name'];


        if (id !== undefined) {
            // this.$el.append('<span class="task-gantt-item-sorting-name">'+id+'</span>');

            this.$el.prop('id', "task-gantt-item-sorting-" + id + "");
            this.$el.prop('data-id', id);
            this.$el.prop('grouping', true);
            this.$el.prop('allowRowHover', true);
        }
        else{
            this.$el.append('<span class="task-gantt-item-sorting-name"></span>');
        }

        if (self.parent.ItemsSorted){
            this.$el.prop('grouping', true);
            this.$el.append('<i class="fa fa-tasks" aria-hidden="true"></i>');

            this.$el.sortable({

                connectWith: ".task-gantt-items",
                items: 'div:not(.ui-state-disabled-notsort)',
                cancel: ".ui-state-disabled",


            });
            this.$el.toggleClass('ui-state-disabled-notsort');

        }

        var fold_self = self.record['fold_self'];
        if (self.items_sorted) {
            if (fold_self) {
                this.$el.css({'display': 'none'});
            }
        }




    },

    renderElement: function () {
        this._super();
        this.$el.data('record', this);

    }
});


function sorted (gantt, ItemsSorted) {

    var self = gantt;


    if (ItemsSorted) {

        var sortable_type = "group";

        var sortable = self.$('.task-gantt-items');
            sortable.sortable({
                placeholder: "ui-state-highlight",
                cursor: 'move',
                items: 'div:not(.ui-state-disabled):not(.ui-state-disabled-group)',
                cancel: ".ui-state-disabled",
                tolerance: "pointer",
                connectWith: '.task-gantt-sorting-item',


            stop: function (event, ui) {

                framework.blockUI();

                // self.TimeToLeft = $('.task-gantt-timeline').scrollLeft();
                self.ScrollToTop = $('.task-gantt').scrollTop();

                var record = ui.item.data('record');

                if (record){

                    var test2 = $.contains(self.$el[0], record.$el[0]);
                    var index = self.widgets.indexOf(record);

                    if (index >= 0 && test2) {

                    var record_id = record.record['id'];
                    var subtask_record_project_id = record.record['subtask_project_id'];
                    var project_id = record.record['project_id'];


                    var previous_id = false;
                    var previous_record = false;


                    //Sorting or Grouping
                    //Grouping Parent Element
                    if (ui.item[0].parentElement) {

                        if (ui.item[0].parentElement.hasOwnProperty('grouping')){
                            if (ui.item[0].parentElement.hasOwnProperty('data-id')) {
                                previous_id = ui.item[0].parentElement['data-id'];
                                previous_record = ui.item[0].parentElement['id'];

                            }

                        }

                    }


                    var sorting_ids = false;
                    //Sorting Parent Element
                    if (ui.item[0].previousSibling) {
                        if (ui.item[0].previousSibling.hasOwnProperty('sorting')) {
                            sorting_ids = sortable.sortable('toArray', {attribute: 'id'});
                        }
                    }


                    var record_el = $("#" + previous_record);
                    var record_data = record_el.data('record');


                    var data = {};

                    if (sorting_ids) {
                        record_id = false;
                        var sorting_to = [];
                        var i = 0;
                        _.each(sorting_ids, function (record, i) {

                              var record_el = $("#" + record);
                              var record_data = record_el.data('record');

                              if (record_data) {
                                  i++;
                                  var sorting_element = {
                                      id : record_data.record['id'],
                                      seq: i
                                  };

                                  sorting_to.push(sorting_element)

                              }
                        });
                            var task_model = self.state.modelName;

                            self._rpc({
                                    model: task_model,
                                    method: 'sorting_update',
                                    args: [sorting_to, subtask_record_project_id, project_id],
                                    context: self.state.contexts
                                })
                                .then(function(ev) {
                                    framework.unblockUI();
                                    self.trigger_up('gantt_refresh_after_change',ev );
                            });


                        return;


                    }


                    data['parent_id'] = previous_id;

                    //Save and refresh after change
                    self._rpc({
                            model: self.state.modelName,
                            method: 'write',
                            args: [[record_id], data],
                            context: self.state.contexts
                        })
                        .then(function(ev) {
                            framework.unblockUI();
                            self.trigger_up('gantt_refresh_after_change',ev );
                    });

                }
                else{
                    framework.unblockUI();
                    self.trigger_up('gantt_refresh_after_change');
                }

                }





            },

                start: function (event, ui) {
                    var record = ui.item.data('record');

                    if (record){


                        var index = self.widgets.indexOf(record);
                        var test2 = $.contains(self.$el[0], record.$el[0]);

                        if (index >= 0 && test2) {

                            var record_project_id = record.record['project_id'];
                            var record_parent_id = record.record['parent_id'];
                            if (record_parent_id){
                                record_parent_id = record_parent_id[0];
                            }

                            var record_id = record.record['id'];

                            $("#task-gantt-item-sorting-" + record_id + "").remove();


                            var sortedIDs = $(".task-gantt-items").sortable('toArray', {attribute: 'id'});

                            _.each(sortedIDs, function (record) {


                                var record_el = $("#" + record);
                                var record_data = record_el.data('record');

                                if (record_data) {

                                    var project_id = record_data.record['project_id'];
                                    var parent_id = record_data.record['parent_id'];
                                    if (parent_id){
                                        parent_id = parent_id[0];
                                    }

                                    var state_disaable = false;
                                    if (project_id !== record_project_id) {

                                        // record_data.$el.css({'opacity': 0.0});
                                        record_data.$el.toggleClass('ui-state-disabled');

                                        state_disaable = true;


                                    }

                                    if (sortable_type === "group" && state_disaable == false ){

                                        if (parent_id !== record_parent_id ) {
                                            record_data.$el.toggleClass('ui-state-disabled');

                                        }

                                    }



                                }
                            });

                                self.$('.task-gantt-items').sortable("refresh");


                        }else{
                            framework.unblockUI();
                            self.do_search(self.last_domains, self.last_contexts, self.last_group_bys, self.options);

                        }


                    }else{
                        framework.unblockUI();
                        self.do_search(self.last_domains, self.last_contexts, self.last_group_bys, self.options);


                    }



                }





            }


        )




    }
}




return {
    sorted: sorted,
    GanttListSortingItem : GanttListSortingItem

};


});