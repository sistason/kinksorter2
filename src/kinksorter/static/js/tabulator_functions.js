/*
var newstorages_built = false;
var newstorage_table_ids = [];
var storage_table_storage_data = {};

var merge_movie = function(row){
    var movie_id = row.getData().movie_id;
    $.ajax({
        url: '/movie/merge',
        data: {movie_id: movie_id},
        success: function(data){
            $("#mainstorage_tabulator").tabulator("addRow", data, true);
            var movie_id = row.getData().movie_id;
            row.update({'status': 'in_main', 'movie_id': -1});
            row.update({'movie_id': movie_id});
        }
     });
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
                $("#mainstorage_tabulator").tabulator("addRow", row.getData(), true);
                row.update({'status': 'in_main', 'movie_id': -1});
                row.update({'movie_id': movie_id});
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
                //FIXME: Check this works
            });
        }
    });
};

var merge_good_movies = function(storage_id){
    var rows = $("#newstorages_"+storage_id+"_tabulator").tabulator("getRows", true);

    var good_rows = {};
    rows.forEach(function(row){
        var row_data = row.getData();
        if (row_data.status == 'okay')
            good_rows[row.getData().movie_id] = row;
    });

    merge_multiple_movies(good_rows);
};

var rescan_storage = function(storage_id) {
    $.ajax({
        url: "/storage/update",
        data: {storage_id: storage_id}
    });
};

var reset_storage = function(storage_id) {
    $.ajax({
        url: "/storage/reset",
        data: {storage_id: storage_id},
        success: function(data) {
            // clear Storage and update MainStorage, which is cleaned by the backend
            var $storage = $(".newstorages_" + storage_id + "_tabulator").tabulator('clearData');
            update_table(0);
        }
    });
};

var recognize_storage = function(storage_id, force) {
    // Run /rec on all unrecognized movies. Force sets all movies to 0 and recognizes them
    var $tabulator = $("#newstorages_"+storage_id+"_tabulator");
    var rows = $tabulator.tabulator("getRows", true);

    if (force){
        $.ajax({
            url: "/storage/rerecognize",
            data: {storage_id: storage_id},
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

var set_newstorage_header = function(current_data){
    //TODO: jqueryize
        var id_ = current_data['storage_id'];
        var new_column_header = "Storage <span contenteditable class='storage_name''>" +
            current_data['storage_name'] + "</span><br /><span class='storage_params'> (" +
            current_data['storage_movies_count'] + " titles)" +
            ((current_data['storage_read_only']) ? " [read_only]" : "") + "</span>";

        $(".newstorages_" + id_ + " .column_header").html(new_column_header);
        $(".newstorages_" + id_ + " .column_header .storage_name").blur(function(){
            change_storage_name(id_, $(this).text())});
};
var change_storage_name = function(storage_id, name){
    $.ajax({
        url: '/storage/change_name',
        data: {'storage_id': storage_id,
               'new_storage_name': name}
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

var add_storage = function(e) {
    $.ajax({
        url: "/storage/add",
        data: $(this).serialize(),
        success: function(data) {
            var storage_id = data.storage_id;
            newstorage_table_ids.push(storage_id);

            build_newstorage_container(storage_id);
            build_newstorage_tabulator(storage_id);
            parse_update_tables_response([data], storage_id);
        },
        error: function(xhr, status, error){
           //TODO: show status/errors
        }
    });
    e.preventDefault();
};

var build_newstorage_container = function(storage_id){
    var base_class = "newstorages_" + storage_id;
    $("#newstorages_container").append(
        "<hr />" +
        "<div class='"+base_class+" newstorages'>" +
            "<table class='column_header_container'>" +
                "<tr>" +
                    "<td class='img_add_storage'>" +
                        "<img title='Add all good movies' class='img_functions' " +
                            "src='/static/img/move_to_main.png' onClick='merge_good_movies(" + storage_id + ")' />" +
                    "</td>" +
                    "<td class='column_header'>" +
                        "<span class='storage_name'>_</span>" +
                        "<br /><span class='storage_params'>&nbsp;</span>" +
                    "</td>" +
                    "<td class='img_delete_storage'>" +
                        "<img title='Delete storage' class='img_functions' src='/static/img/delete.png' "+
                            "onClick='delete_storage(" + storage_id + ")' />" +
                    "</td>" +
                "</tr>"+
            "</table>" +
            "<table class='column_function_container'>" +
                "<tr>" +
                    "<td class='rescan_storage '>" +
                        //TODO: Mouseover: verbose explanation
                        "<div class='click_function' onClick='rescan_storage(" + storage_id + ")'>" +
                            "<img title='Rescan storage' src='/static/img/rescan_storage.png'  />" +
                            "<span class=img_description>Rescan storage</span>"+
                        "</div>" +
                    "</td>" +
                    "<td class='rescan_storage '>" +
                        "<div class='click_function' onClick='reset_storage(" + storage_id + ")'>" +
                            "<img title='Force Rescan storage' src='/static/img/force_rescan_storage.png' />" +
                            "<span class=img_description>Reset storage</span>"+
                        "</div>" +
                    "</td>" +
                    "<td class='recognize_movies '>" +
                        "<div class='click_function' onClick='recognize_storage(" + storage_id + ")'>" +
                            "<img title='Recognize unrecognized movies' src='/static/img/recognize_storage.png' />" +
                            "<span class=img_description>Recognize unrecognized</span>" +
                        "</div>" +
                    "</td>" +
                    "<td class='recognize_movies' " +
                        "<div class='click_function' onClick='recognize_storage(" + storage_id + ", true)'>" +
                            "<img title='Force recognize all movies' src='/static/img/force_recognize_storage.png' />" +
                            "<span class=img_description>Re-recognize storage</span>" +
                        "</div>" +
                    "</td>" +
                "</tr></table>" +
            "<div id='"+base_class+"_tabulator'></div>" +
        "</div>");
};

var build_newstorages_add = function(){
    $("#newstorages_container").append(
        "<div class='newstorages_0 newstorages'>" +
            "<form class='add_storage' action='add_storage'>" +
                "<table><tr>" +
                    "<td class='submit'>" +
                        "<input type='image' name='submit' src='/static/img/add_storage.png' " +
                            "class='img_functions' alt='Submit' />" +
                    "</td>" +
                    "<td>" +
                        "<input class='input_name' name='name' placeholder='New storage name' />&nbsp;" +
                        "<input class='input_path' name='storage_path' placeholder='New storage path'  />" +
                        "<input id='read_only' type='checkbox' value='False' name='read_only' />" +
                            "<label for='read_only'>read_only?</label>" +
                    "</td>" +
                "</tr></table>" +
            "</form>" +
        "</div>");
    $('.add_storage').submit(add_storage);
};

var build_newstorages = function(){
    build_newstorages_add();

    for (var index in newstorage_table_ids) {
        var storage_id = newstorage_table_ids[index];
        build_newstorage_container(storage_id);
        build_newstorage_tabulator(storage_id);
    }
    newstorages_built = true;
};

var build_newstorage_tabulator = function(storage_id){
    $("#newstorages_" + storage_id + "_tabulator").tabulator({
        //height:"100%",

        movableColumns: true,
        fitColumns: true,

        cellEdited: modify_movie,
        rowFormatter: format_row,

        tooltips: show_tooltips,

        columns: [
                {title: "", field: 'movie_id', formatter: format_options, minWidth: 65, width: 65,
                    formatterParams: {storage_id: storage_id}, headerSort: false, frozen: true,
                    cellClick: watch_video},
                {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                    minWidth: 300, variableHeight: true},
                {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
                {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
                {title: "Site", field: "scene_site", width: 150},
                {title: "API", field: "api", minWidth: 80, width: 80}
        ]
    });
};
*/

var mainstorage_built = false;
var set_mainstorage_header = function(options) {};


var build_mainstorage = function() {
    $("#mainstorage_tabulator").tabulator({
        movableColumns: true,
        fitColumns: true,

        cellEdited: modify_movie,

        tooltips: show_tooltips,

        columns: [
            {title: "", field: 'movie_id', formatter: format_options, minWidth: 48, width: 48,
                formatterParams: {storage_id: 0}, headerSort: false, frozen: true,
                cellClick: watch_video},
            {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                minWidth: 300, variableHeight: true},
            {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
            {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
            {title: "Site", field: "scene_site", width: 150},
            {title: "API", field: "api", minWidth: 80, width: 80},
            {title: "Storage", field: "storage_name", minWidth: 100, width: 100},

            {title: 'Status', field: "status", visible: false},
            {title: 'Movie ID', field: "movie_id", visible: false}
        ],
        tableBuilt: function(){mainstorage_built = true;}
    });
};
