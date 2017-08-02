var newstorages_built = false;
var newstorage_table_ids = [];
var storage_table_storage_data = {};

var merge_movie = function(movie_id){
    $.ajax({
           url: '/movie/merge',
           data: {movie_id: movie_id}
     });
};

var merge_good_movies = function(storage_id){
    var data = $("#newstorages_"+storage_id+"_tabulator").tabulator("getData", true);

    data.forEach(function(current_data){
        if (current_data['status'] == 'okay'){
            merge_movie(current_data['movie_id']);
            current_data.delete();
        }
    });
};


var set_newstorage_header = function(current_data){
        var id_ = current_data['storage_id'];
        var new_column_header = "Storage <span contenteditable class='storage_name' style='font-weight: bold;'>" +
            current_data['storage_name'] + "</span> (" +
            current_data['storage_movies_count'] + " titles)" +
            ((current_data['storage_read_only']) ? " [read_only]" : "");

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
    var column = cell.getColumn().getField();
    var row = cell.getRow();
    var new_scene_name = '', new_scene_id = '';

    if (column == 'title') {
        new_scene_name = cell.getValue();
    } else if (column == 'scene_id') {
        new_scene_id = cell.getValue();
    }

    $.ajax({
            type: 'GET',
            url: '/movie/recognize',
            data: {movie_id: row.getData().movie_id,
                  new_scene_name: new_scene_name,
                  new_scene_id: new_scene_id
                 },
            success: row.update,
            error: function(xhr, status, error)
            {
               row.getElement().css('background-color', 'red');
               //$(this).find($(".response")).css('background', 'red').text(xhr.responseText);
            }
     });
};

var format_options = function(cell, params){
    var del = "<img alt=Delete width='15px' src='/static/img/delete.png' class=delete onClick='delete_movie(" +
        cell.getValue() + ")'  />";
    var add = "<img alt=Add width='15px' src='/static/img/add.png' onClick='merge_movie(" +
        cell.getValue() + ")' />";
    var watch = "<a href='"+ cell.getData().watch_scene +"'><img width='15px' src='/static/img/watch.png'/></a>";

    return ((cell.getData().status == 'okay') ? add + "&nbsp;" : "") + del + "&nbsp;" + watch;
};
var format_row = function(row){
    var color = {'unrecognized': '#ffc0c0', 'duplicate': '#ffffc0', 'okay': '#c0ffc0'};
    row.getElement().css({"background-color": color[row.getData().status]});
};

var build_newstorages = function(){
    for (index in newstorage_table_ids){
        var storage_id = newstorage_table_ids[index];
        var base_class = "newstorages_" + storage_id;
        $("#newstorages_container").append(
            "<div class='"+base_class+" newstorages'>" +
                "<table class='column_header_container'><tr>" +
                    "<td>" +
                        "<img title='Add all good movies' class='img_functions' " +
                            "src='/static/img/add.png' onClick='merge_good_movies(" + storage_id + ")' />" +
                    "</td>" +
                    "<td>" +
                        "<p class='column_header'>column_header</p>" +
                    "</td>" +
                    "<td>" +
                        "<img title='Delete storage' class='img_functions' src='/static/img/delete.png'"+
                            "onClick='delete_storage(" + storage_id + ")' /></td>" +
                "</tr></table>" +
                "<div id='"+base_class+"_tabulator'></div>" +
            "</div>");

        $("#" + base_class + "_tabulator").tabulator({
            //height:"100%",

            movableColumns: true,
            fitColumns: true,

            cellEdited: modify_movie,
            rowFormatter: format_row,

            tooltips: show_tooltips,

            columns: [
                    {title: "", field: 'movie_id', formatter: format_options, minWidth: 75, width: 75,
                        headerSort: false, frozen: true},
                    {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                        minWidth: 300, variableHeight: true},
                    {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
                    {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
                    {title: "Site", field: "scene_site", width: 150},
                    {title: "API", field: "api", minWidth: 80, width: 80},

                    {title: 'Status', field: "status", visible: false},
                    {title: 'Movie ID', field: "movie_id", visible: false}
            ]
            //TODO: Delete item, from table and from database
            //TODO: Delete/add/modify storage
        });
    }
    newstorages_built = true;
};
