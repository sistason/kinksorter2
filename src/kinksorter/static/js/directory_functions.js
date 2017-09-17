var toggle_update_tables = function() {
    var $cb_refresh = $('#cb_refresh');
    if (!update_tables_timer_id){
        update_tables_timer_id = setInterval(update_tables, 10000);
        $cb_refresh.prop('src', '/static/img/refresh_on.png')
    }
    else {
        clearInterval(update_tables_timer_id);
        update_tables_timer_id = null;
        $cb_refresh.prop('src', '/static/img/refresh_off.png')
    }
};
var sort_target = function() {
    var action = $('#sort_target_action').val();
    $.ajax({
        url: '/sort',
        data: {'action': action},
        error: function(xhr, status, error){
            var error_response = error;
            var $sorting_response = $('#sorting_response');
            $sorting_response.text(error_response).show();
            $sorting_response.fadeOut(5000);
        }
    });
};
var revert_target = function() {
    $.ajax({
        url: '/revert',
        success: function(data){

        },
        error: function(xhr, status, error){
            var error_response = error;
            var $sorting_response = $('#revert_response');
            $sorting_response.text(error_response).show();
            $sorting_response.fadeOut(5000);
        }
    });
};

var build_sorting = function() {
    $('#cb_refresh').click(toggle_update_tables);

    $('#img_sort_target').click(sort_target);

    $('#img_revert_target').click(revert_target);

    $('#img_add_directory').click(add_porn_directory);

    $('#sorting_response').hide();
    $('#revert_response').hide();
    $('#add_directory_response').hide();
};