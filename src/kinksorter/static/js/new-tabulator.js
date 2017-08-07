var newstorages_built = false;
var newstorage_table_ids = [];
var storage_table_storage_data = {};

var merge_movie = function(row, storage_id){
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

var merge_good_movies = function(storage_id){
    var rows = $("#newstorages_"+storage_id+"_tabulator").tabulator("getRows", true);

    rows.forEach(function(row){
        var row_data = row.getData();
        if (row_data.status == 'okay'){
            merge_movie(row, storage_id);
        }
    });
    //$("#mainstorage_tabulator").tabulator("redraw");
};

var rescan_storage = function(storage_id, force) {

};

var recognize_storage = function(storage_id, force) {

};

var set_newstorage_header = function(current_data){
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
            parse_update_tables_response(data, storage_id);
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
                    "<td rowspan='2' class='img_add_storage'>" +
                        "<img title='Add all good movies' class='img_functions' " +
                            "src='/static/img/move_to_main.png' onClick='merge_good_movies(" + storage_id + ")' />" +
                    "</td>" +
                    //TODO: rescan_storage, full_rescan_storage, recognize_all_unrecognized, recognize_all_again
                    "<td class='img_rescan_storage'>" +
                        "<img title='Rescan storage' class='img_functions' " +
                            "src='/static/img/rescan_storage.png' onClick='rescan_storage(" + storage_id + ")' />" +
                    "</td>" +
                    "<td class='img_recognize_movies'>" +
                        "<img title='Recognize unrecognized movies' class='img_functions' " +
                            "src='/static/img/recognize_storage.png' onClick='recognize_storage(" + storage_id + ")' />" +
                    "</td>" +
                    "<td rowspan='2' class='column_header'>" +
                        "<span class='storage_name'>_</span>" +
                        "<br /><span class='storage_params'>&nbsp;</span>" +
                    "</td>" +
                    "<td rowspan='2' class='img_delete_storage'>" +
                        "<img title='Delete storage' class='img_functions' src='/static/img/delete.png'"+
                            "onClick='delete_storage(" + storage_id + ")' /></td>" +
                "</tr><tr>" +
                    "<td class='img_rescan_storage'>" +
                        "<img title='Force Rescan storage' class='img_functions img_force' " +
                            "src='/static/img/force_rescan_storage.png' " +
                            "onClick='rescan_storage(" + storage_id + ", true)' />" +
                        "<br /><span class=img_description >force</span>" +
                    "</td>" +
                    "<td class='img_recognize_movies'>" +
                        "<img title='Force recognize all movies' class='img_functions img_force' " +
                            "src='/static/img/force_recognize_storage.png' " +
                            "onClick='recognize_storage(" + storage_id + ", true)' />" +
                        "<br /><span class=img_description >force</span>" +
                    "</td>" +
                "</tr></table>" +
            "<div id='"+base_class+"_tabulator'></div>" +
        "</div>");
};

var build_newstorages_add = function(){
    $("#newstorages_container").append(
        "<div class='newstorages_0 newstorages'>" +
            "<form class='add_storage' action='add_storage'>" +
                "<table class='column_header_container'><tr>" +
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
                    formatterParams: {storage_id: storage_id}, headerSort: false, frozen: true},
                {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                    minWidth: 300, variableHeight: true},
                {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
                {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
                {title: "Site", field: "scene_site", width: 150},
                {title: "API", field: "api", minWidth: 80, width: 80}
        ],
        tableBuilt: function(){newstorages_built = true;}
    });
};

