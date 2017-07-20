$(document).ready( function() {

    var show_tooltips = function(cell) {
        return cell.getRow().getData().full_path;
    };

    var updated_row = function(row){
        //TODO: recalculate movie_counts
    };

    var format_options = function(cell, params){
        //TODO: not working, clicks catched?
        var del = "<img width='10px' onClick='delete_movie(" + cell.getValue() + ")' src='/static/img/delete.png' class=delete />";
        var add = "<img width='10px' onClick='add_movie_to_main(" + cell.getValue() + ")' src='/static/img/add.png' />";
        var watch = "<a href='"+ cell.getRow().getData().watch_scene +"'>watch</a>";

        return add + "&nbsp;" + del + "&nbsp;" + watch;
    };

    var delete_movie = function(movie_id){
        $.ajax({
               url: '/movie/delete',
               data: {movie_id: movie_id}
         });
    };

    var add_movie_to_main = function(movie_id){
        $.ajax({
               url: '/movie/add_to_main',
               data: {movie_id: movie_id}
         });
    };

    var format_row = function(row){
        var color = {'unrecognized': '(255, 0, 0, .3)', 'duplicate': '(255, 255, 0, .3)', 'okay': '(0, 255, 0, .3)'};
        row.getElement().css({"background": "rgba"+color[row.getData().status]});
    };

    var add_all_green_to_main = function(storage_id){
        var data = $("#newstorages-tabulator-" + storage_id).tabulator("getData");

        for (index in data){
            var current_data = data[index];
            if (current_data['status'] == 'green'){
                add_movie_to_main(current_data['movie_id']);
                current_data.delete();
            }
        }

    };

    var format_date = function(cell, params){
        var ts = cell.getValue();
        if (ts == null)
            return;

        //FIXME: exceptions if not int?
        var date = new Date(parseInt(ts)*1000);
        return date.toLocaleFormat("%Y-%m-%d");
    };

    var modify_movie = function(cell){
        var row = cell.getRow();

        $.ajax({
               type: 'GET',
               url: '/movie/recognize',
               data: {movie_id: row.getData().id,
                      new_scene_name: row.getCell('title').getValue(),
                      new_scene_id: row.getCell('scene_id').getValue()
                     },
               context: this,
               //dataType: "text",
               error: function(xhr, status, error)
               {
                   //TODO
                   //$(this).find($(".response")).css('background', 'red').text(xhr.responseText);
               }
         });
    };

    $('.delete').click(function(e) {
        return window.confirm("Are you sure to delete that?");
    });

    // TODO: check if updating breaks editing. Shouldn't.
    // TODO: Problem: updateOrAdd doesn't delete. But setData def. breaks editing, right?
    var update = function(event){
        $("#newstorages-tabulator").tabulator("updateOrAddData", "/storage/get_all_storages", {}, "GET");
    };

    var newstorage_tables = [];
    var newstorage_table_data = {};
    var parse_table_data = function(url, params, data){
        var return_data = [];

        for (index in data){
            var current_data = data[index];

            if (current_data['type'] == 'storage') {
                newstorage_table_data[current_data['storage_id']] = current_data;
                set_storage_header(current_data);
            }
            else {
                return_data[return_data.length] = current_data;
            }
        }
        return return_data;
    };

    var set_storage_header = function(current_data){
        var new_column_header = "Storage <span contenteditable class='storage_name' style='font-weight: bold;'>" +
            current_data['storage_name'] + "</span> (" + current_data['storage_movies_count'] + " titles)";

        var id_ = current_data['storage_id'];
        $(".newstorages_" + id_ + " .column_header").html(new_column_header);
        $(".newstorages_" + id_ + " .column_header .storage_name").blur(function(id_){
            change_storage_name(id_, $(this).text())});
    };

    var change_storage_name = function(storage_id, name){
        $.ajax({
            url: '/storage/change_name',
            data: {'storage_id': '',
                   'new_storage_name': name}

        });
    };

    $.ajax({
        url:'/storage/get_storage_ids',
        success: function(data){
            newstorage_tables = data;


            for (index in newstorage_tables){
                var storage_id = newstorage_tables[index];
                var base_class = "newstorages_" + storage_id;
                $("#newstorages_tabulators").append(
                    "<div class='"+base_class+"'>" +
                        "<p class='column_header'>column_header</p>" +
                        "<div id='"+base_class+"_tabulator'></div>" +
                    "</div><br />");

                $("#" + base_class + "_tabulator").tabulator({
                    ajaxURL: "/storage/get_storage",
                    ajaxParams: {"storage_id": storage_id},
                    ajaxConfig: "GET",
                    ajaxResponse: parse_table_data,

                    fitColumns: true,
                    movableColumns: true,
                    columnVertAlign: "middle",

                    rowUpdated: updated_row,
                    cellEdited: modify_movie,
                    rowFormatter: format_row,

                    tooltips: show_tooltips,

                    columns: [
                            {title: "Options", field: 'movie_id', formatter: format_options},
                            {title: "API", field: "api", minWidth: 80, width: 80},
                            {title: "Title", columns: [
                                {title: "Site", field: "scene_site"},
                                {title: "Date", field: "scene_date", formatter: format_date},
                                {title: "ID", field: "scene_id", editor: true}
                            ]},
                            {title: 'Title', field: "scene_title", editor: true},
                            {title: 'Status', field: "status", visible: false},
                            {title: 'Movie ID', field: "movie_id", visible: false}
                    ]
                    //TODO: Delete item, from table and from database
                    //TODO: Delete/add/modify storage
                });
            }
        }
    });


});