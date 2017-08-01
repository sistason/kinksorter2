var mainstorage_built = false;
var set_mainstorage_header = function(options) {};

var format_options = function(cell, params){
    //TODO: not working, clicks catched?
    var del = "<img width='15px' onClick='delete_movie(" + cell.getValue() + ")' src='/static/img/delete.png' class=delete />";
    var add = "<img width='15px' onClick='add_movie_to_main(" + cell.getValue() + ")' src='/static/img/add.png' />";
    var watch = "<a href='"+ cell.getRow().getData().watch_scene +"'><img width='15px' src='/static/img/watch.png'/></a>";

    return add + "&nbsp;" + del + "&nbsp;" + watch;
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

var build_mainstorage = function() {
    $("#mainstorage_tabulator").tabulator({
        //height:"100%",

        fitColumns: true,
        movableColumns: true,
        columnVertAlign: "middle",

        cellEdited: modify_movie,

        tooltips: show_tooltips,

        columns: [
            {title: "Storage", field: "storage", minWidth: 100, width: 100},
            {title: "Options", field: 'movie_id', formatter: format_options,
                minWidth: 80, width: 80, headerSort:false},
            {title: 'Title', field: "title", editor: true},
            {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
            {title: "Date", field: "scene_date", formatter: format_date},
            {title: "Site", field: "scene_site"},
            {title: "API", field: "api", minWidth: 80, width: 80},


            {title: 'Status', field: "status", visible: false},
            {title: 'Movie ID', field: "movie_id", visible: false}
        ]

        //TODO: Delete item, from table and from database
        //TODO: Delete/add/modify storage
    });
    mainstorage_built = true;
};
