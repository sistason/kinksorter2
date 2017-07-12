$(document).ready( function() {

    var show_tooltips = function(cell) {
        return cell.getRow().getData().path;
    };

    var updated_row = function(row){
        //recalculate movie_counts
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

    // TODO: check if updating breaks editing. Shouldn't.
    // TODO: Problem: updateOrAdd doesn't delete. But setData def. breaks editing, right?
    var update = function(event){
        $("#storage-tabulator").tabulator("updateOrAddData", "/storage/get_all_storages", {}, "GET");
    };

    $("#mainstorage-tabulator").tabulator({
        ajaxURL: "/storage/get_main_storage",
        ajaxConfig: "GET",

        fitColumns: true,
        movableColumns: true,
        columnVertAlign: "middle",

        rowUpdated: updated_row,
        cellEdited: modify_movie,

        tooltips: show_tooltips,

        columns: [
            {title: "Storage", field: "storage", minWidth: 100, width: 100},
            {title: "API", field: "api", minWidth: 80, width:80},
            {title: "Options"},
            {title: "Title", field: "scene_title", columns: [
                {title: "Site", field: "scene_site"},
                {title: "Date", filed: "scene_date"},
                {title: "ID", filed: "scene_id"}
                ]
            },
            {title: "Watch"}
        ]

        //TODO: Delete item, from table and from database
        //TODO: Delete/add/modify storage
    });
});