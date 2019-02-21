odoo.define('web_gantt_native.TimeLineArrowDraw', function (require) {
    "use strict";


    function LinkWrapper (prop) {

        var LinkWrapper = $('<div class="gantt_timeline_link_wrapper" class="gantt_timeline_link_wrapper_'+prop.dir+'"></div>');
            LinkWrapper.css({'top': prop.top + "px"});
            LinkWrapper.css({'left': prop.left + "px"});
            LinkWrapper.css({'width': prop.width + "px"});
            LinkWrapper.css({'height': prop.height + "px"});

            if (prop["align_center"]){
                LinkWrapper.css({'text-align': "center"});
                prop.left = prop.left-2;
            }

            LinkWrapper.css({'left': prop.left + "px"});
            return LinkWrapper

    }

    function LinkCircle (path) {

        var cycleL = $('<i class="fa fa-circle" style="font-size: 8px;" aria-hidden="true"></i>');
        cycleL.css({'vertical-align': 4 +"px"});
        cycleL.css({'color': path.color});


        return cycleL;
    }

    function LinkLine (prop, dir ) {

        var Px = $('<div class="gantt_timeline_link_'+dir+'"></div>');
            Px.css({'background-color': prop.color});
            Px.css({'width': prop.width + "px"});
            Px.css({'height': prop.height + "px"});

            if (prop.critical_path){
                Px.css({'box-shadow': "0 0 2px 1px #f30b0b6e"});
            }


            return Px
    }

    function LinkArrow (path) {

        var caretRight = $('<i class="fa fa-caret-'+path.dir+'" style="font-size: 12px;" aria-hidden="true"></i>');
        caretRight.css({'vertical-align': 2 +"px"});

        caretRight.css({'color': path.color});
        return caretRight
    }

    function LinkStartPoint (prop) {

        var path = {"top": 0, "left": 0, "width": 0, "height": 0, "color": prop.color, "type": prop.type, "dir": 0,
        "align_center" : 1};

        path.critical_path = prop.critical_path;
        path.width = 8;
        path.height = 16;
        path.dir = "S1";
        path.top = prop.from_obj_top + path.width/2 + 2;

        if (prop.type === "FF" || prop.type === "FS") {
            path.left = prop.from_obj_left + prop.margin_stop+2;
        }

        if (prop.type === "SS" || prop.type === "SF") {
            path.left = prop.from_obj_left - prop.margin_start;
        }

        return path;

    }

    function LinkEndPoint(prop) {

        var path = {"top": 0, "left": 0, "width": 0, "height": 0, "color": prop.color, "type": prop.type, "dir": 0,
        "align_center" : 0};


        if (prop.type === "FF" || prop.type === "SF") {

            path.left = prop.to_obj_left + prop.margin_stop+1;
            path.width = 10;
            path.height = 16;
            path.align_center = 1;


            if (prop.directionY === "up") {
                path.dir = "up";

                if (prop.directionX === "right") {
                   path.top = prop.to_obj_top+prop.margin_arrow_down;
                }

                if (prop.directionX === "left") {
                    path.top = prop.to_obj_top+prop.margin_arrow_down;
                }

            }
            if (prop.directionY === "down") {
                path.dir = "down";

                if (prop.directionX === "right") {
                   path.top = prop.to_obj_top-prop.margin_arrow_top;
                }

                if (prop.directionX === "left") {
                    path.top = prop.to_obj_top-prop.margin_arrow_top;
                }

            }

        }

        if (prop.type === "SS" || prop.type === "FS") {

            path.top = prop.to_obj_top;
            path.left = prop.to_obj_left - prop.margin_start-1;
            path.width = 10;
            path.height = 16;
            path.align_center = 1;
            path.dir = "down";

            if (prop.directionY === "up") {
                path.dir = "up";

                if (prop.directionX === "right") {
                   path.top = prop.to_obj_top+prop.margin_arrow_down;
                }

                if (prop.directionX === "left") {
                    path.top = prop.to_obj_top+prop.margin_arrow_down;
                }

            }
            if (prop.directionY === "down") {
                path.dir = "down";

                if (prop.directionX === "right") {
                   path.top = prop.to_obj_top-prop.margin_arrow_top;
                }

                if (prop.directionX === "left") {
                    path.top = prop.to_obj_top-prop.margin_arrow_top;
                }

            }
        }


        return path;

    }

    function CalcStep(prop, from, to) {

        var step = undefined;

        if (to.top < from.top){
            //go up
            if (to.left > from.left){
                //go right
                if (prop.type === "SF" || prop.type === "SS") {
                    step = ["up", "right", "up"];
                }

                if (prop.type === "FS" || prop.type === "FF") {
                    step = ["right", "up"];
                }

            }

            if (to.left < from.left){
                //go left
                if (prop.type === "SF" || prop.type === "SS") {
                    step = ["left", "up"];
                }

                if (prop.type === "FS" || prop.type === "FF") {
                    step = ["up", "left","up"];
                }

            }

            if (to.left === from.left){
                step = ["up"];
            }
        }

        if (to.top > from.top){
            //go down
            if (to.left >= from.left){
                //go right
                if (prop.type === "SF" || prop.type === "SS") {
                     step = ["down","right", "down"];
                }


                if (prop.type === "FS" || prop.type === "FF") {
                    step = ["right", "down"];
                }
            }

            if (to.left < from.left){
                //go left
                if (prop.type === "SF" || prop.type === "SS") {
                    step = ["left","down"];
                }

                if (prop.type === "FS" || prop.type === "FF") {
                    step = ["down", "left","down"];
                }

            }
        }

        return step;

    }

    function CalcPath(prop, from, to, dir, step) {

         var path = {"top": 0, "left": 0, "width": 0, "height": 0, "color": prop.color, "type": prop.type, "dir": 0,
        "align_center" : 0};

         path.critical_path = prop.critical_path;

         // var margin_to_top = 10;

        if (dir === "up"){

            if (to) {
                path.top = to.top + 10;
                path.left = to.left + 4;
                path.width = prop.line_size;
                path.height = (from.top - path.top) + 2;
            } else{
                path.top = from.top - 10;
                path.left = from.left+ 3;
                path.width = prop.line_size;
                path.height = (from.top - path.top) + 4;
            }
        }

        if (dir === "down"){

            if (to) {
                path.top = from.top;
                path.left = to.left + 4;
                path.width =  prop.line_size;
                path.height = (to.top - path.top) + 6;
            } else{


                path.top = from.top+10;
                path.left = from.left+ 3;
                path.width = prop.line_size;
                path.height =  10;
            }


        }


        if (dir === "right"){
                path.top = from.top;
                path.left = from.left;
                path.width = (to.left - from.left) + 4;
                path.height = prop.line_size;

               if (prop.directionY === "down") {
                    path.top = from.top+10;
               }

               if (prop.type === "FF" || prop.type === "FS") {
                    path.top = from.top+6;
                    path.left = from.left+7;
                    path.width = (to.left - from.left) - 2;

                    if (path.width < 0){
                        path.width = 0
                    }

               }



        }


        if (dir === "left"){

                path.top = from.top + 5;
                path.left = to.left + 4;
                path.width = (from.left - path.left);
                path.height = prop.line_size;

                if (prop.type === "FF" || prop.type === "FS") {
                    path.top = from.top;
                }

                if (prop.type === "FS" || prop.type === "FF") {
                    if (prop.directionY === "down") {
                         path.top = from.top + from.width + 6;
                    }
                }


        }

        return path;

    }


    function drawLink (from_obj, to_obj, type) {

        //FS
        var prop = {
            "from_obj_left": 0,

            "to_obj_left": 0,

            "to_obj_top": 0,
            "from_obj_top": 0,

            "link_dif": 0,
            "color": 0,
            "directionX" : 0,
            "directionY" : 0,
            "type": type
        };

        if (type === "FS") {
            prop.from_obj_left = from_obj.task_stop_pxscale;
            prop.to_obj_left = to_obj.task_start_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 55;
            prop.color = '#7a7a7a';

        }

        //SS
        if (type === "SS") {
            prop.from_obj_left = from_obj.task_start_pxscale;
            prop.to_obj_left = to_obj.task_start_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 20;

            prop.color = '#63cbe9';
        }

        //FF
        if (type === "FF") {
            prop.from_obj_left = from_obj.task_stop_pxscale;
            prop.to_obj_left = to_obj.task_stop_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 20;

            prop.color = '#4cd565';
        }

        //SF
        if (type === "SF") {
            prop.from_obj_left = from_obj.task_start_pxscale;
            prop.to_obj_left = to_obj.task_stop_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 20;

            prop.color = '#d08d73';
        }

        //directionX
        prop.directionX = "right"; //X = RIGHT
        if ((prop.to_obj_left - prop.from_obj_left) <= prop.link_dif) { //X = LEFT
            prop.directionX = "left";
        }

        //directionY
        prop.directionY = "up"; //Y = UP
        if (prop.to_obj_top > prop.from_obj_top) { //Y = DOWN
            prop.directionY = "down";
        }

        //Critical path
        prop.critical_path = undefined;
        if (from_obj.critical_path && to_obj.critical_path && from_obj.cp_shows){

            prop.critical_path = 1
        }

        var LinkWrapperR = [];

        prop["line_size"] = 2;
        prop["margin_stop"] = 5;
        prop["margin_start"] = 12;
        prop["circle_width"] = 8;
        prop["circle_height"] = 16;
        prop["margin_arrow_down"] = 12;
        prop["margin_arrow_top"] = 4;


        var s1 = LinkStartPoint(prop);
        var LinkWrapperS1 = LinkWrapper(s1);
        var S1_cicrcle = LinkCircle(s1);
        LinkWrapperS1.append(S1_cicrcle);
        LinkWrapperR.push(LinkWrapperS1);

        var e1 = LinkEndPoint(prop);
        var LinkWrapperE1 = LinkWrapper(e1);
        var E1_arrow = LinkArrow(e1);
        LinkWrapperE1.append(E1_arrow);
        LinkWrapperR.push(LinkWrapperE1);

        var steps = CalcStep(prop, s1, e1 );
        var paths = [];

        if (steps){

            var steps_i = steps.length;

            if (steps_i === 3){
                paths.push(CalcPath(prop, s1, undefined, steps[0], 0));
                paths.push(CalcPath(prop, paths[0], e1, steps[1], 1));
                paths.push(CalcPath(prop, paths[1], e1, steps[2], 2));
            }

            if (steps_i === 1){
                paths.push(CalcPath(prop, s1, e1, steps[0], 0));
            }

            if (steps_i === 2){
                paths.push(CalcPath(prop, s1, e1, steps[0], 0));
                paths.push(CalcPath(prop, paths[0], e1, steps[1], 1));
            }

            _.each(paths, function(path) {

                LinkWrapperR.push(LinkWrapper(path).append(LinkLine(path)));

            })

        }


        return LinkWrapperR

    }


    return {drawLink: drawLink };

});
