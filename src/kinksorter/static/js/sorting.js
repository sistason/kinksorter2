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
    $('#img_sort_target').click(sort_target);

    $('.sort_action_explanation').accordion({header: 'span', heightStyle: "content"});
    var show_explanation = function(){
        var $accordion = $('.sort_action_explanation');

        var actions = ['link', 'move', 'list', 'cmd'];
        var action = $('#sort_target_action').val();

        if (actions.indexOf(action) == -1){
            $accordion.hide();
            return
        }
        $accordion.accordion('option', 'active', actions.findIndex(function(a_){return a_==action}));
        $accordion.show();
    };
    $('#sort_target_action').change(show_explanation).trigger("change");

    $('#img_revert_target').click(revert_target);

    $('#img_add_directory').click(add_porn_directory);

    $('#sorting_response').hide();
    $('#revert_response').hide();
    $('#add_directory_response').hide();
};

$(document).ready(function(){
    // start update, so the ajax can run while building the storages
    update_tables();

    build_sorting();

    build_target_porn_directory_container();
    build_target_porn_directory_tabulator();
    tables_built = true;

    setInterval(update_current_task, 1000);
    update_tables_timer_id = setInterval(update_tables, 10000);

    $('.delete').click(function(e) {
        return window.confirm("Are you sure to delete that?");
    });
    $('.tab_container .sorting').addClass('active');
});