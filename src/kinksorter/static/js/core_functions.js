var update_tables_timer_id;

var add_porn_directory = function(e) {
    var $porn_directory_name = $('.porn_directory_0 .input_name');
    var $porn_directory_path = $('.porn_directory_0 .input_path');
    var $porn_directory_read_only = $('.porn_directory_0 .input_ro');

    $.ajax({
        url: "/porn_directory/add",
        data: {
            porn_directory_name: $porn_directory_name.val(),
            porn_directory_path: $porn_directory_path.val(),
            porn_directory_read_only: $porn_directory_read_only.val()
        },
        success: function(data) {
            var porn_directory_id = data.porn_directory_id;
            porn_directory_table_ids.push(porn_directory_id);

            build_porn_directory_container(porn_directory_id);
            build_porn_directory_tabulator(porn_directory_id);
            parse_update_tables_response(data, porn_directory_id);

            $('#add_porn_directory_response_text')
                .css({'color': 'green'})
                .text('New porn directory successfully added!');
            var $response = $('.add_porn_directory_response');
            $response.show('slow');
            var hide_response_delayed = function() {
                $response.slideUp(1000);
            };
            setInterval(hide_response_delayed, 5000);

        },
        error: function(xhr, status, error){
            $('#add_porn_directory_response_text')
                .css({'color': 'red'})
                .text(xhr.responseText);
            var $response = $('.add_porn_directory_response');
            $response.show('slow');
            var hide_response_delayed = function() {
                $response.slideUp(1000);
            };
            setInterval(hide_response_delayed, 10000);
        }
    });
};
var change_porn_directory_name = function(porn_directory_id, name){
    $.ajax({
        url: '/porn_directory/change_name',
        data: {'porn_directory_id': porn_directory_id,
               'new_porn_directory_name': name}
    });
};
var delete_porn_directory = function(porn_directory_id){
    $.ajax({
        url: '/porn_directory/delete',
        data: {porn_directory_id: porn_directory_id},
        success: function(){
            var index = porn_directory_table_ids.findIndex(function(id){return id==porn_directory_id});
            porn_directory_table_ids.splice(index, 1);
            porn_directory_tabulators.splice(index, 1);

            $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator('clearData');
            $("div.porn_directory_" + porn_directory_id).empty();

            $("#target_porn_directory_tabulator").tabulator("getRows").forEach(function(mainrow){
                if (mainrow.getData().porn_directory_id == porn_directory_id)
                    mainrow.delete();
            });
        }
    });
};
var clear_target_porn_directory = function(){
    $.ajax({
        url: '/porn_directory/clear_target',
        success: function(data){
            $("#target_porn_directory_tabulator").tabulator('clearData');
            update_tables();
            // update status TODO: doesn't work
            porn_directory_table_ids.forEach(function(porn_directory_id){
                var rows = $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator('getRows');
                for (var i=0; i<rows.length; i++){
                    var current_row = rows[i];
                    if (current_row.getData().status == 'in_main'){
                        current_row.update({movie_id: 0});
                        current_row.update({movie_id: movie_id});
                    }
                }
            });

        }
    });
};

var scan_target = function() {
    $.ajax({
        url: '/porn_directory/scan_target/'
    });
};
var delete_movie = function(row) {
    var movie_id = row.getData().movie_id;
    $.ajax({
        url: '/movie/delete',
        data: {movie_id: movie_id},
        success: function(data){
            row.delete();
            var targetrows = $("#target_porn_directory_tabulator").tabulator("getRows");
            for (var i=0; i<targetrows.length; i++){
                var targetrow = targetrows[i];
                if (targetrow.getData().movie_id == movie_id) {
                    targetrow.delete();
                    break;
                }
            }
        }
    });
};
var modify_movie = function(cell){
    var field = cell.getField();
    var row = cell.getRow();
    var new_scene_name = '', new_scene_id = '';

    if (field == 'title') {
        new_scene_name = cell.getValue();
    } else if (field == 'scene_id') {
        new_scene_id = cell.getValue();
    }

    if (new_scene_id == '' && new_scene_name == '')
        return;

    $.ajax({
            type: 'GET',
            url: '/movie/recognize',
            data: {
                movie_id: row.getData().movie_id,
                new_scene_name: new_scene_name,
                new_scene_id: new_scene_id
            },
            success: function(data){
                // TODO: differ between row being in dir or target_dir, both need to be updated (if in_target)
                row.update({'movie_id': -1});
                row.update(data);

                if (data.in_target) {
                    var targetrows = $("#target_porn_directory_tabulator").tabulator("getRows");
                    targetrows.forEach(function (targetrow) {
                        if (targetrow.getData().movie_id == data.movie_id)
                            targetrow.update(data);
                    });
                }
            },
            error: function(xhr, status, error) {
                row.getElement().css('background-color', 'red');
            }
     });
};
var move_movie_to_target = function(row){
    var movie_id = row.getData().movie_id;
    $.ajax({
        url: '/movie/merge',
        data: {movie_id: movie_id},
        success: function(data){
            $("#target_porn_directory_tabulator").tabulator("addRow", data, true);
            row.update({'movie_id': -1, 'status': ''});
            row.update(data);
        }
     });
};
var remove_movie_from_target = function(row) {
    $.ajax({
        url: '/movie/remove_from_target',
        data: {movie_id: row.getData().movie_id},
        success: function(data){
            row.delete();

            // Rebuild options/background for the movie in each tabulator
            porn_directory_table_ids.forEach(function(porn_directory_id){
                var rows = $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator('getRows');
                for (var i=0; i<rows.length; i++){
                    var current_row = rows[i];
                    if (current_row.getData().movie_id == row.getData().movie_id){
                        //TODO: status != okay! status not in_target, otherwise unknown.
                        //   Rewrite okay/unrecognized to redetect here
                        current_row.update({status: 'okay', movie_id: 1});
                        current_row.update({movie_id: movie_id});

                        format_row(current_row);
                        break;
                    }
                }
            });
        }
    });
};

var recognize_multiple = function(rows){
    var movie_ids = [];
    for (var key in rows)
        if (rows.hasOwnProperty(key))
            movie_ids.push(key);

    $.ajax({
        type: 'GET',
        url: '/movie/recognize_multiple',
        data: {movie_ids: movie_ids},
        success: function(data){
            data.forEach(function(movie) {
                var row = rows[movie.movie_id];
                row.update({'movie_id': -1});
                row.update(data);
            });
        }
    });
};
var merge_good_movies = function(porn_directory_id){
    var rows = $("#porn_directory_"+porn_directory_id+"_tabulator").tabulator("getRows", true);

    var good_rows = {};
    rows.forEach(function(row){
        var row_data = row.getData();
        if (row_data.status == 'okay')
            good_rows[row.getData().movie_id] = row;
    });

    merge_multiple_movies(good_rows);
};
var merge_multiple_movies = function(rows){
    var movie_ids = [];
    for (var key in rows)
        if (rows.hasOwnProperty(key))
            movie_ids.push(key);

    $.ajax({
        url: '/movie/merge_multiple',
        data: {movie_ids: movie_ids},
        success: function(data){
            data.forEach(function(movie_id) {
                var row = rows[movie_id];
                row.update({'status': 'duplicate', 'movie_id': -1, 'in_target': true});
                $("#target_porn_directory_tabulator").tabulator("addRow", row.getData(), true);
                row.update({'movie_id': movie_id});
            });
        }
    });

};
var reset_porn_directory = function(porn_directory_id) {
    $.ajax({
        url: "/porn_directory/reset",
        data: {porn_directory_id: porn_directory_id},
        success: function(data) {
            // clear PornDirectory and update TargetPornDirectory, which is cleaned by the backend
            $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator('clearData');
            update_table(0);
        }
    });
};
var rescan_porn_directory = function(porn_directory_id) {
    $.ajax({
        url: "/porn_directory/update",
        data: {porn_directory_id: porn_directory_id}
    });
};
var recognize_porn_directory = function(porn_directory_id, force) {
    // Run /rec on all unrecognized movies. Force sets all movies to 0 and recognizes them
    var $tabulator = $("#porn_directory_"+porn_directory_id+"_tabulator");
    var rows = $tabulator.tabulator("getRows", true);

    if (force){
        $.ajax({
            url: "/porn_directory/rerecognize",
            data: {porn_directory_id: porn_directory_id},
            success: function(data) {
                $tabulator.tabulator("clearData");
                $tabulator.tabulator("setData", data);

                update_tables(0);
            }
        });
    }
    else {
        var bad_rows = {};
        rows.forEach(function(row){
            var row_data = row.getData();
            if (row_data.status == 'unrecognized')
                bad_rows[row.getData().movie_id] = row;
        });

        recognize_multiple(bad_rows);
    }
};

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
var initial_parse_update_tables_response = function(data, porn_directory_id) {
    if (!tables_built) {
        setTimeout(function () {initial_parse_update_tables_response(data, porn_directory_id)}, 10);
        return;
    }
    parse_update_tables_response(data, porn_directory_id);
};
var parse_update_tables_response = function(data, porn_directory_id){
    var $tabulator;
    if (porn_directory_id == 0){
        $tabulator = $("#target_porn_directory_tabulator");
        set_target_porn_directory_header(data);
    }
    else {
        $tabulator = $("#porn_directory_" + porn_directory_id + "_tabulator");
        set_porn_directory_header(data, porn_directory_id);
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
    var porn_directory_ids = porn_directory_table_ids.concat([0]);
    porn_directory_ids.forEach(function (porn_directory_id) {
        update_table(porn_directory_id);
    });
};
var update_table = function(porn_directory_id){
    $.ajax({
        url: "/porn_directory/get",
        data: {"porn_directory_id": porn_directory_id},
        dataType: 'json',
        success: function(data, textStats, jqXHR){
            initial_parse_update_tables_response(data, porn_directory_id);
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

$(document).ready(function() {
    $('#cb_refresh').click(toggle_update_tables);
});
