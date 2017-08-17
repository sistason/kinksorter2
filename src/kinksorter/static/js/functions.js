var show_tooltips = function(cell) {
        return cell.getData().full_path;
    };
var format_row = function(row){
    var color = {'unrecognized': '#ffc0c0', 'in_main': '#ffffc0', 'okay': '#c0ffc0'};
    row.getElement().css({"background-color": color[row.getData().status]});
};
var delete_movie = function(row) {
    $.ajax({
        url: '/movie/delete',
        data: {movie_id: row.getData().movie_id},
        success: function(data){
            row.delete();
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
var format_options = function(cell, params){
    var $container = $('<div>', {'class': 'options_container'});

    var $del = $('<img>');
    if (params.storage_id != 0){
        $del.attr({alt: "Delete", src: '/static/img/delete.png', 'class': 'img_options delete'});
        $del.click(function(){
            delete_movie(cell.getRow())
        });
        var $add = $('<img>', {alt: "Add", src: '/static/img/move_to_main.png', 'class': 'img_options'});
        $add.click(function(){
            merge_movie(cell.getRow(), params.storage_id)
        });
        if (cell.getData().status == 'okay') {
            $container.append($add);
            $container.append('&nbsp;');
        }
    }
    else {
        $del.attr({alt: "Remove", src: '/static/img/remove_from_main.png', 'class': 'img_options'});
        $del.click(function(){remove_movie_from_main(cell.getRow())});
    }
    $container.append($del);
    $container.append('&nbsp;');

    var $watch = $('<a>', {href: cell.getData().watch_scene});
    $watch.append($('<img>', {src: '/static/img/watch.png', 'class': 'img_options'}));
    $container.append($watch);

    return $container;
};
var delete_storage = function(storage_id){
    $.ajax({
        url: '/storage/delete',
        data: {storage_id: storage_id},
        success: function(){
            $("#newstorages_" + storage_id + "_tabulator").tabulator('clearData"');
            $("div.newstorages_" + storage_id).empty();
            //TODO: remove all storage-movies from MainStorage
        }
    });
};
var format_date = function(cell, params){
    var ts = parseInt(cell.getValue()) || null;
    if (ts == null)
        return;

    var date = new Date(ts*1000);
    return date.toISOString().slice(0,10);
};

// TODO: check if updating breaks editing. Shouldn't.
var update_tables = function(event){
    var storage_ids = newstorage_table_ids.concat([0]);
    storage_ids.forEach(function (storage_id) {
        console.log('updating table', storage_id);
        update_table(storage_id);
    });
};
var update_table = function(storage_id){
    $.ajax({
        url: "/storage/get_storage",
        data: {"storage_id": storage_id},
        dataType: 'json',
        success: function(data, textStats, jqXHR){
            parse_update_tables_response(data, storage_id);
        }
    });
};
var parse_update_tables_response = function(data, storage_id){
    var $tabulator;
    if (storage_id == 0) {
        if (! mainstorage_built){
            setTimeout(function(){parse_update_tables_response(data, storage_id)}, 10);
            return;
        }
        $tabulator = $("#mainstorage_tabulator");
    }
    else {
        if (! newstorages_built){
                setTimeout(function(){parse_update_tables_response(data, storage_id)}, 10);
                return;
        }
        $tabulator = $("#newstorages_" + storage_id + "_tabulator");
    }

    var table_data = $tabulator.tabulator('getData');
    var table_length = table_data.length;
    var modified_data = [], added_data = [], deleted_data = table_data;

    for (var i=0; i<data.length; i++){
        var current_element = data[i];

        if (current_element.type == 'storage') {
            if (storage_id == 0)
                set_mainstorage_header(current_element);
            else
                set_newstorage_header(current_element);
        }
        else {
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


$(document).ready(function(){
    $.ajax({
        url: '/storage/get_storage_ids',
        success: function (data) {
            newstorage_table_ids = data;

            // start update, so the ajax can run while building the storages
            update_tables();

            build_mainstorage();
            build_newstorages();

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

           $('#mainstorage_container').css("width",(percentage-2) + "%");
           $('#newstorages_container').css("width",(mainPercentage-2) + "%");
           $('#ghostbar').remove();
           $(document).unbind('mousemove');
           dragging = false;

           newstorage_tables.forEach(function(i){
               $("#newstorages_"+i+"_tabulator").tabulator("redraw");
           });
           $("#mainstorage_tabulator").tabulator("redraw");
       }
    });

    $('.delete').click(function(e) {
        return window.confirm("Are you sure to delete that?");
    });
});
