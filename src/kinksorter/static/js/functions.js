var show_tooltips = function(cell) {
        return cell.getData().full_path;
    };
var delete_movie = function(movie_id) {
    $.ajax({
        url: '/movie/delete',
        data: {movie_id: movie_id}
    });
};
var delete_storage = function(storage_id){
    $.ajax({
        url: '/storage/delete',
        data: {storage_id: storage_id}
    });
};
var format_date = function(cell, params){
        var ts = cell.getValue();
        if (ts == null)
            return;

        //FIXME: exceptions if not int?
        var date = new Date(parseInt(ts)*1000);
        return date.toISOString().slice(0,10);
    };


$('.delete').click(function(e) {
        return window.confirm("Are you sure to delete that?");
    });

// TODO: check if updating breaks editing. Shouldn't.
var update_tables = function(event){
    var storage_ids = newstorage_table_ids.concat([0]);
    storage_ids.forEach(function (storage_id) {
        $.ajax({
            url: "/storage/get_storage",
            data: {"storage_id": storage_id},
            dataType: 'json',
            success: function(data, textStats, jqXHR){
                parse_update_tables_response(data, storage_id);
            }
        });
    });
};

var parse_update_tables_response = function(data, storage_id){
    var tabulator;
    if (storage_id == 0) {
        if (! mainstorage_built){
            setTimeout(function(){parse_update_tables_response(data, storage_id)}, 10);
            return;
        }
        tabulator = $("#mainstorage_tabulator");
    }
    else {
        if (! newstorages_built){
                setTimeout(function(){parse_update_tables_response(data, storage_id)}, 10);
                return;
        }
        tabulator = $("#newstorages_" + storage_id + "_tabulator");
    }

    var table_data = tabulator.tabulator('getData');
    var table_length = table_data.length;
    var modified_data = [], added_data = [], deleted_data = table_data;

    for (var i=0; i<data.length; i++){
        var current_element = data[i];

        if (current_element.type == 'storage') {
            storage_table_storage_data[storage_id] = current_element;
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
        tabulator.tabulator("setData", added_data);
    }
    else {
        var modified_and_added_data = modified_data.concat(added_data);
        tabulator.tabulator("updateOrAddData", modified_and_added_data);
    }
    for (d=0; d<deleted_data.length; d++)
        tabulator.tabulator("deleteRow", deleted_data[d].id);

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

            //setInterval(update_tables, 10000);
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

           $('#mainstorage_container').css("width",(percentage-1) + "%");
           $('#newstorages_container').css("width",(mainPercentage-1) + "%");
           $('#ghostbar').remove();
           $(document).unbind('mousemove');
           dragging = false;

           newstorage_tables.forEach(function(i){
               $("#newstorages_"+i+"_tabulator").tabulator("redraw");
           });
           $("#mainstorage_tabulator").tabulator("redraw");
       }
    });
});
