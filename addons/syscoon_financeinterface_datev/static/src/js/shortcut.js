$.shortcut = function(key, callback, args) {
    $(document).keydown(function(e) {
        if(!args) args=[]; // IE barks when args is null
        console.log(e.keyCode)
        if((e.keyCode == key.charCodeAt(0) || e.keyCode == key)) {
            callback.apply(this, args);
            return false;
        }
    });
};

//give the enter button the tab function
$.shortcut('113', function() {
    $('.oe_form_button_edit').each(function() {
        if($(this).parents('div:hidden').length == 0) {
            $(this).trigger('click');
        }
    });
});
