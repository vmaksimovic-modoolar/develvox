odoo.define('web_gantt_native.NativeGanttModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel');
var GanttToolField = require('web_gantt_native.ToolField');
var GanttTimeLineGhost = require('web_gantt_native.Ghost');
var GanttTimeLineFirst = require('web_gantt_native.BarFirst');
var framework = require('web.framework');

return AbstractModel.extend({

    init: function () {
        this._super.apply(this, arguments);
        this.gantt = null;

    },

    get: function () {
        return _.extend({}, this.gantt);
    },

    load: function (params) {
        this.modelName = params.modelName;
        this.fields_view  = params.fieldsView;
        this.gantt = {
            modelName : params.modelName,
            group_bys : params.groupedBy,
            domains : params.domain || [],
            contexts :  params.context || {},
            fields_view : params.fieldsView,
            fields : params.fields,
            pager : []

        }

        return this._do_load();

    },

        //---1---//
    _do_load: function () {

        var domains = this.gantt.domains;
        var contexts = this.gantt.contexts;
        var group_bys = this.gantt.group_bys;

        var self = this;

        self.main_group_id_name = self.fields_view.arch.attrs.main_group_id_name;
        self.action_menu = self.fields_view.arch.attrs.action_menu;

        // Sort allow only if Group by project and domain search by project.
        // Project get from XML = main_group_id_name = "project_id"

        self.ItemsSorted = false;
        if (group_bys.length === 1){

            if (group_bys[0] === self.main_group_id_name){
                 self.ItemsSorted = true;
            }
            if (domains.length > 0){
                if (domains[0][0] !== self.main_group_id_name){
                 self.ItemsSorted = false;
                }
            }

            if (domains.length > 1){
                self.ItemsSorted = false;
            }
        }

        if (self.fields_view.arch.attrs.no_group_sort_mode){
            self.ItemsSorted = false;
        }

        // Tree View only if group by main_group_id_name
        self.TreeView = false;

        if (group_bys.length === 1) {

            if (group_bys[0] === self.main_group_id_name || group_bys[-1] === self.main_group_id_name) {
                self.TreeView = true;
            }
        }

        if (group_bys.length > 1 ) {

            if (group_bys[group_bys.length-1] === self.main_group_id_name) {
                self.TreeView = true;
            }
        }




        // self.last_domains = domains;
        // self.last_contexts = contexts;
        // self.last_group_bys = group_bys;
        // self.date_start = null;
        // self.date_stop = null;

        var n_group_bys = [];

        // select the group by - we can select group by from attribute where XML if not determinate dafault group
        // for model

        if (this.fields_view.arch.attrs.default_group_by) {
           n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
        }

        if (group_bys.length) {
            n_group_bys = group_bys;
        }



        var getFields = GanttToolField.getFields(self, n_group_bys);
        self.model_fields = getFields["model_fields"];
        self.model_fields_dict = getFields["model_fields_dict"];

        var fields = self.model_fields;
        fields.push('display_name');

        // this.fields_view.arch.attrs.default_group_by
        var export_wizard = false;

        if (self.fields_view.arch.attrs.hasOwnProperty('export_wizard')){
            export_wizard = self.fields_view.arch.attrs.export_wizard
        }


        self.gantt.data = {
            ItemsSorted : self.ItemsSorted,
            ExportWizard : export_wizard,
            TreeView : self.TreeView,
            Main_Group_Id_Name : self.main_group_id_name,
            Action_Menu : self.action_menu,
            model_fields : fields,
            model_fields_dict : self.model_fields_dict,
            model_fields_view : self.fields_view,

        };

        var limit_view = 0;
        if (self.fields_view.arch.attrs.hasOwnProperty('limit_view')){
            limit_view = parseInt(self.fields_view.arch.attrs.limit_view)
        }

        if(self.gantt.pager.limit){
            limit_view = self.gantt.pager.limit
        }


        return this._rpc({
                model: this.modelName,
                method: 'search_read',
                context: this.gantt.contexts,
                domain: this.gantt.domains,
                fields: _.uniq(fields),
                limit: limit_view
            })
            .then(function (data) {
                self.gantt.pager.limit = limit_view;
                return self.on_data_loaded_count(data, n_group_bys);
            });

    },


    on_data_loaded_count: function(tasks, group_bys) {
        var self = this;

        return this._rpc({
                model: this.modelName,
                method: 'search_count',
                args: [this.gantt.domains],
                context: this.gantt.contexts,
            })
            .then(function (result) {
                self.gantt.pager.records = result;

                if (self.gantt.pager.records > self.gantt.pager.limit){
                    self.gantt.data.ItemsSorted = false
                }

                return self.on_data_loaded_dummy(tasks, group_bys);
            });


    },



    on_data_loaded_dummy: function(tasks, group_bys) {
        var self = this;
        return self.on_data_loaded_info(tasks, group_bys);
    },

    //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_info: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var info_model = self.fields_view.arch.attrs.info_model;
        var info_task_id = "task_id";

        if (info_model) {

            return this._rpc({
                    model: info_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [[info_task_id, 'in', _.uniq(ids)]],
                    fields: _.uniq([info_task_id,"start", "end", "left_up","left_down","right_up","right_down","show"])
                })
                .then(function (result) {

                    if (result){
                        result = _.map(result, function(info) {

                        if (info.task_id){
                            info.task_id = info.task_id[0];
                            return info;
                        }
                        });
                    }



                    self.gantt.data.task_info = result;
                    return self.on_data_loaded_predecessor(tasks, group_bys);
                });
            }
        else{
            return self.on_data_loaded_predecessor(tasks, group_bys);
        }

    },





    //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_predecessor: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var predecessor_model = self.fields_view.arch.attrs.predecessor_model;
        var predecessor_task_id = self.fields_view.arch.attrs.predecessor_task_id;
        var predecessor_parent_task_id = self.fields_view.arch.attrs.predecessor_parent_task_id;
        var predecessor_type = self.fields_view.arch.attrs.predecessor_type;

        if (predecessor_model) {

            return this._rpc({
                    model: predecessor_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [[predecessor_task_id, 'in', _.uniq(ids)]],
                    fields: _.uniq([predecessor_task_id, predecessor_parent_task_id, predecessor_type])
                })
                .then(function (result) {
                    self.gantt.data.predecessor = result;
                    return self.on_data_loaded_ghost(tasks, group_bys);
                });
            }
        else{
            return self.on_data_loaded_ghost(tasks, group_bys);
        }

    },

            //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_ghost: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var ghost_id = self.fields_view.arch.attrs.ghost_id;
        var ghost_model = self.fields_view.arch.attrs.ghost_model;
        var ghost_name = self.fields_view.arch.attrs.ghost_name;
        var ghost_date_start = self.fields_view.arch.attrs.ghost_date_start;
        var ghost_date_end = self.fields_view.arch.attrs.ghost_date_end;
        var ghost_durations = self.fields_view.arch.attrs.ghost_durations;

        if (ghost_model) {
            return this._rpc({
                    model: ghost_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [[ghost_id, 'in', _.uniq(ids)]],
                    fields: _.uniq([ghost_id ,ghost_name, ghost_date_start, ghost_date_end, ghost_durations])
                })
                .then(function (result) {
                    self.gantt.data.Ghost = result;
                    self.gantt.data.Ghost_Data = GanttTimeLineGhost.get_data_ghosts(self);

                    return self.on_data_loaded_barfirst(tasks, group_bys);
                });

        }
        else{
            return self.on_data_loaded_barfirst(tasks, group_bys);
        }

    },

    on_data_loaded_barfirst: function(tasks, group_bys) {

        var self = this;

        if (self.ItemsSorted) {

            var barfirst_field = "project_id";

            var barfirst_field_ids = _.pluck(tasks, "project_id");

            var ids = _.pluck(barfirst_field_ids, "0");

            var barfirst_model = "project.project";
            var barfirst_name = "name";
            var barfirst_date_start = "date_start";
            var barfirst_date_end = "date_end";


            return this._rpc({
                    model: barfirst_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [['id', 'in', _.uniq(ids)]],
                    fields: _.uniq(['id', barfirst_name, barfirst_date_start, barfirst_date_end])
                })
                .then(function (result) {
                    self.gantt.data.BarFirst = result;
                    self.gantt.data.BarFirst_Data = GanttTimeLineFirst.get_data_barfirst(self);

                    return self.on_data_loaded_name_get(tasks, group_bys);
                });

        }
        else{
            return self.on_data_loaded_name_get(tasks, group_bys);
        }

    },


        //Get name get from model form name field
    on_data_loaded_name_get: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        return this._rpc({
                model: this.modelName,
                method: 'name_get',
                args: [ids],
                context: this.gantt.contexts,
            })
            .then(function (names) {
                var ntasks = _.map(tasks, function(task) {
                        return _.extend({__name: _.detect(names, function(name) { return name[0] == task.id; })[1]}, task);
                });

                // return self.gantt_render(ntasks, group_bys);
                self.gantt.data.ntasks = ntasks;
                self.gantt.data.group_bys = group_bys;
                return self.get_second_sort_data(ntasks, group_bys);

            });


    },


    get_second_sort_data: function(tasks, group_bys) {

            var self = this;
            self.gantt.data["second_sort"] = undefined;
            var gantt_attrs = self.fields_view.arch.attrs;

            var link_field = gantt_attrs["second_seq_link_field"];

            if (group_bys.length === 1 && group_bys[0] === link_field) {

                var ids = [];
                _.map(tasks, function (result) {

                    if (result[link_field]) {
                        ids.push(result[link_field][0]);
                    }
                });

                var s_model =  gantt_attrs["second_seq_model"];
                var s_field =  gantt_attrs["second_seq_field"];

                return this._rpc({
                    model: s_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [['id', 'in', _.uniq(ids)]],
                    fields: _.uniq(['id',s_field])
                })
                .then(function (result) {

                    self.gantt.data["second_sort"] = result;
                });
            }
            return self.get_main_group_data(tasks, group_bys);

    },


    get_main_group_data: function(tasks, group_bys) {

            var self = this;
            self.gantt.data["main_group"] = undefined;
            var gantt_attrs = self.fields_view.arch.attrs;

            var main_id = gantt_attrs["main_group_id_name"];
            var s_model =  gantt_attrs["main_group_model"];
            var s_field = ["id", "name","fold_group"];

            if (group_bys.length === 1 && group_bys[0] === main_id && s_model) {

                var ids = [];
                _.map(tasks, function (result) {

                    if (result[main_id]) {
                        ids.push(result[main_id][0]);
                    }
                });



                return this._rpc({
                    model: s_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [['id', 'in', _.uniq(ids)]],
                    fields: _.uniq(s_field)
                })
                .then(function (result) {
                    self.gantt.data["main_group"] = result;


                    // return result
                    return true

                });

            }


            return true

    },


    // this.gantt.data.push();







    reload: function (handle, params) {
        if (params.domain) {
            this.gantt.domains = params.domain;
        }
        if (params.context) {
            this.gantt.contexts = params.context;
        }
        if (params.groupBy) {
            this.gantt.group_bys = params.groupBy;
        }
        return this._do_load();
    },

});

});
