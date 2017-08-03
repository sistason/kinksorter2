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
            row.update({status: 'in_main'});

            var options_cell = row.getCell('movie_id');
            var options = format_options(options_cell, {storage_id: storage_id});
            options_cell.getElement().find('span.options_container').replaceWith(options);
            //FIXME: Why do I have to do this manually?
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

var set_newstorage_header = function(current_data){
        var id_ = current_data['storage_id'];
        var new_column_header = "Storage <span contenteditable class='storage_name' style='font-weight: bold;'>" +
            current_data['storage_name'] + "</span><br /> (" +
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
                row.update(data);

                var options_cell = row.getCell('movie_id');
                var options = format_options(options_cell, {storage_id: 5});
                options_cell.getElement().find('span.options_container').replaceWith(options);
                //FIXME: Why do I have to do this manually?

            },
            error: function(xhr, status, error)
            {
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
      success: function() {
          //TODO: reload page? or dynamic?
       }
    });

    e.preventDefault();

};

var build_newstorages = function(){
    var $newstorages_container = $("#newstorages_container");
    var storage_id = 0;
    var base_class = "newstorages_" + storage_id;
    $newstorages_container.append(
            "<div class='"+base_class+" newstorages'>" +
                "<form class='add_storage' action='add_storage'>" +
                    "<table class='column_header_container'><tr>" +
                        "<td>" +
                            "<input type='image' name='submit' src='/static/img/add_storage.png' " +
                                "class='img_functions' alt='Submit' />" +
                        "</td>" +
                        "<td>" +
                            "<input height=10px name='name' placeholder='New storage name' /><br />" +
                            "<input height=10px name='storage_path' placeholder='New storage path'  />" +
                        "</td>" +
                        "<td>" +
                            "<input id='read_only' type='checkbox' value='False' name='read_only' />" +
                                "<label for='read_only'>read_only?</label>" +
                        "</td>" +
                    "</tr></table>" +
                "</form>" +
            "</div>"
    );
    $('.add_storage').submit(add_storage);

    for (index in newstorage_table_ids){
        storage_id = newstorage_table_ids[index];
        base_class = "newstorages_" + storage_id;
        $newstorages_container.append(
            "<div class='"+base_class+" newstorages'>" +
                "<table class='column_header_container'><tr>" +
                    "<td>" +
                        "<img title='Add all good movies' class='img_functions' " +
                            "src='/static/img/move_to_main.png' onClick='merge_good_movies(" + storage_id + ")' />" +
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
    }

};
