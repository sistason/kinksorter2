
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

var recreate_target_porn_directory = function(e) {
    console.log(e);
    $.ajax({
        url: "/porn_directory/recreate_target",
    })
};


var change_porn_directory_name = function(porn_directory_id, $element){
    $.ajax({
        url: '/porn_directory/change_name',
        data: {'porn_directory_id': porn_directory_id,
               'new_porn_directory_name': $element.text()},
        success: function(data){
            $element.css({'border': '1 green solid'});
            var normalize = function() {
                $element.css({'border': ''});
            };
            setInterval(normalize, 2000);
        },
        error: function(data){
            $element.css({'border': '1 red solid'});
            var normalize = function() {
                $element.css({'border': ''});
            };
            setInterval(normalize, 2000);
        }
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
var change_sort_file_format = function(){
    $.ajax({
        url: '/porn_directory/change_sort_file_format',
        data: {file_format: $('#sort_file_format').val()},
        success: function(data){
            $('#sort_file_format').css({'border': '1 green solid'});
            var normalize = function() {
                $('#sort_file_format').css({'border': ''});
            };
            setInterval(normalize, 2000);
        },
        error: function(data){
            $('#sort_file_format').css({'border': '1 red solid'});
            var normalize = function() {
                $('#sort_file_format').css({'border': ''});
            };
            setInterval(normalize, 2000);
        }
    });
}

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

var sort_target = function() {
    var action = $('#sort_target_action').val();
    $.ajax({
        url: '/sort_target',
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
        url: '/revert_target',
        success: function(data){
            return;
        },
        error: function(xhr, status, error){
            var error_response = error;
            var $sorting_response = $('#revert_response');
            $sorting_response.text(error_response).show();
            $sorting_response.fadeOut(5000);
        }
    });
};

var rescan_target = function() {
    var $target_porn_directory_path = $('#target_porn_directory_path');
    $.ajax({
        url: '/porn_directory/rescan_target/',
        data: {porn_directory_path: $target_porn_directory_path.val()},
        success: function(data){
            location.reload();
        }
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
