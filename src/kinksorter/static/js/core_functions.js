var porn_directory_table_ids = [];
var tables_built = false;

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
            data: {movie_id: row.getData().movie_id,
                  new_scene_name: new_scene_name,
                  new_scene_id: new_scene_id
                 },
            success: function(data){
                row.update({'movie_id': -1});
                row.update(data);

                //FIXME: Check this works
            },
            error: function(xhr, status, error) {
                row.getElement().css('background-color', 'red');
                //TODO: show status/errors
               //$(this).find($(".response")).css('background', 'red').text(xhr.responseText);
            }
     });
};
var add_porn_directory = function(e) {
    var $porn_directory_name = $('.porn_directory_table_0 .input_name');
    var $porn_directory_path = $('.porn_directory_table_0 .input_path');
    var $porn_directory_read_only = $('.porn_directory_table_0 .input_ro');

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
        },
        error: function(xhr, status, error){
           //TODO: show status/errors
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
var rescan_porn_directory = function(porn_directory_id) {
    $.ajax({
        url: "/porn_directory/update",
        data: {porn_directory_id: porn_directory_id}
    });
};
/*


var delete_movie = function(row) {
    var movie_id = row.getData().movie_id;
    $.ajax({
        url: '/movie/delete',
        data: {movie_id: movie_id},
        success: function(data){
            row.delete();
            var mainrows = $("#mainstorage_tabulator").tabulator("getRows");
            for (var i=0; i<mainrows.length; i++){
                var mainrow = mainrows[i];
                if (mainrow.getData().movie_id == movie_id) {
                    mainrow.delete();
                    break;
                }
            }
        }
    });
};
var remove_movie_from_main = function(row) {
    $.ajax({
        url: '/movie/remove_from_main',
        data: {movie_id: row.getData().movie_id},
        success: function(data){
            row.delete();

            // Rebuild options/background for the movie in each newstorage_table
            newstorage_table_ids.forEach(function(storage_id){
                var rows = $("#newstorages_" + storage_id + "_tabulator").tabulator('getRows');
                for (var i=0; i<rows.length; i++){
                    var current_row = rows[i];
                    if (current_row.getData().movie_id == row.getData().movie_id){
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
*/
var delete_porn_directory = function(porn_directory_id){
    $.ajax({
        url: '/porn_directory/delete',
        data: {porn_directory_id: porn_directory_id},
        success: function(){
            $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator('clearData');
            $("div.porn_directory_" + porn_directory_id).empty();

            $("#target_porn_directory_tabulator").tabulator("getRows").forEach(function(mainrow){
                if (mainrow.getData().porn_directory_id == porn_directory_id)
                    mainrow.delete();
            });
        }
    });
};

var watch_video = function(e, cell){

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
        $tabulator = $("#reference_porn_directory_tabulator");
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


var update_tables = function(event){
    // TODO: check if updating breaks editing. Shouldn't.
    var porn_directory_ids = porn_directory_table_ids.concat([0]);
    porn_directory_ids.forEach(function (porn_directory_id) {
        update_table(porn_directory_id);
    });
};
var update_table = function(porn_directory_id){
    $.ajax({
        url: "/porn_directory/get_porn_directory",
        data: {"porn_directory_id": porn_directory_id},
        dataType: 'json',
        success: function(data, textStats, jqXHR){
            initial_parse_update_tables_response(data, porn_directory_id);
        }
    });
};

$(document).ready(function(){
    $.ajax({
        url: '/porn_directory/get_porn_directory_ids',
        success: function (data) {
            porn_directory_table_ids = data;

            // start update, so the ajax can run while building the storages
            update_tables();

            build_tables();

            //setInterval(update_tables, 20000);
        }
    });

    var i = 0;
    var dragging = false;
    $('#dragbar').mousedown(function(e){
       e.preventDefault();

       dragging = true;
       var main = $('#newstorages_container');
       var ghostbar = $('<div>',
                        {id:'ghostbar',
                         css: {
                                height: main.outerHeight(),
                                top: main.offset().top,
                                left: main.offset().left
                               }
                        }).appendTo('body');

        $(document).mousemove(function(e){
          ghostbar.css("left",e.pageX+2);
       });
    });
    $(document).mouseup(function(e){
       if (dragging) {
           var percentage = (e.pageX / window.innerWidth) * 100;
           var mainPercentage = 100-percentage;

           $('#reference_porn_directory_table_container').css("width",(percentage-2) + "%");
           $('#porn_directory_tables_container').css("width",(mainPercentage-2) + "%");
           $('#ghostbar').remove();
           $(document).unbind('mousemove');
           dragging = false;

           // TODO: necessary?
           porn_directory_table_ids.forEach(function(i){
               $("#porn_directory_"+i+"_tabulator").tabulator("redraw");
           });
           $("#reference_porn_directory_tabulator").tabulator("redraw");
       }
    });

    $('.delete').click(function(e) {
        return window.confirm("Are you sure to delete that?");
    });
});
