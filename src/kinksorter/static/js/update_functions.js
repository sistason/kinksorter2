var update_tables_timer_id;
var porn_directory_table_ids = [];
var porn_directory_tabulators = [];

$(document).ready(function() {
    $('#cb_refresh').click(toggle_update_tables);
});


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
var parse_update_tables_response = function(data, porn_directory_id){
    var $tabulator;
    if (porn_directory_id == 0){
        $tabulator = $("#target_porn_directory_tabulator");

        $("#target_porn_directory_container" + " .porn_directory_params")
        .text(data.porn_directory_path +
            " (" + data.porn_directory_movies_count + " titles)");
        $("#target_porn_directory_container" + " #target_porn_directory_path")
            .attr('placeholder', data.porn_directory_path)

    }
    else {
        $tabulator = $("#porn_directory_" + porn_directory_id + "_tabulator");
        // Abort if the directory_id was not yet build
        if (! $tabulator.length)
            return;
        var $porn_directory_name = $('<span>', {'class': 'porn_directory_name'})
            .text(data.porn_directory_name).prop('contentEditable', true);
        var $porn_directory_params = $('<span>', {'class': 'porn_directory_params'})
            .text(data.porn_directory_path +
                " (" + data.porn_directory_movies_count + " titles)");

        $(".porn_directory_" + porn_directory_id + " .column_header").html("Directory ")
            .append($porn_directory_name).append("<br />").append($porn_directory_params);
        var $name_element = $(".porn_directory_" + porn_directory_id + " .column_header .porn_directory_name")
        $name_element.blur(function(){change_porn_directory_name(porn_directory_id, $name_element)});
    }

    var movies = data.movies;
    var table_data = $tabulator.tabulator('getData');
    var table_length = table_data.length;
    var modified_data = [], added_data = [], deleted_data = table_data;

    for (var i=0; i<movies.length; i++){
        var current_element = movies[i];

        var position = table_data.findIndex(function(o_){
            return o_.movie_id == current_element.movie_id;
        });
        if (position != -1) {
            var row_item = table_data[position];
            current_element.id = row_item.id;

            var different = false;
            for (var key in current_element)
                // skip loop if the property is from prototype
                if (current_element.hasOwnProperty(key))
                    if (current_element[key] != row_item[key]){
                        different = true;
                        break;
                    }
            if (different)
                modified_data.push(current_element);

            table_data.splice(position, 1); //delete found elements here, so any remaining are now-deleted elements
        }
        else {
            current_element.id = table_length;
            table_length += 1;
            added_data.push(current_element);
        }
    }
    if (table_length == added_data.length && modified_data.length == 0){
        // initial load
        $tabulator.tabulator("setData", added_data);
    }
    else {
        var modified_and_added_data = modified_data.concat(added_data);
        $tabulator.tabulator("updateOrAddData", modified_and_added_data);
    }
    for (d=0; d<deleted_data.length; d++)
        $tabulator.tabulator("deleteRow", deleted_data[d].id);
};
var update_tables = function(){
    $.ajax({
        url: '/porn_directory/get_ids',
        success: function(data){
            porn_directory_table_ids = data;
            data.forEach(function (porn_directory_id) {
                update_table(porn_directory_id);
            });
        }
    });

};
var update_table = function(porn_directory_id){
    $.ajax({
        url: "/porn_directory/get",
        data: {"porn_directory_id": porn_directory_id},
        dataType: 'json',
        success: function(data, textStats, jqXHR){
            parse_update_tables_response(data, porn_directory_id);

            if (porn_directory_id == 0) return; // target_directory is definitely build already

            // If tabulator was not build yet, build it now
            if (! $(".porn_directory_" + porn_directory_id).length){
                var $container = $("#porn_directory_tables_container");
                var $porn_directory_container = build_porn_directory_container(porn_directory_id);
                $container.append($porn_directory_container).append($('<hr>'));

                build_porn_directory_tabulator(porn_directory_id);

                // reparse/re-add into newly build tabulator, as it wasn't there (and not filled) before
                parse_update_tables_response(data, porn_directory_id);
            }
        }
    });
};
var update_current_task = function(){
    $.ajax({
        url: '/get_current_task',
        success: function(data){

            var $tasks = $('#current_tasks').empty();
            if (!data.length) {
                $tasks.append($('<span class="current_task_action">').text('Idle'));
                return;
            }

            for (var i=0; i<data.length; i++) {
                if (i != 0)
                    $tasks.append(' + ');

                $tasks.append($('<span class="current_task_action">').text(data[i].action));
                $tasks.append('&nbsp;');

                var running = 'running for '+data[i].running_for+' seconds';
                $tasks.append($('<span>').text(running));

                $tasks.append('&nbsp;');
                $tasks.append('(' + data[i].progress + ')');
            }
        }
    });
};