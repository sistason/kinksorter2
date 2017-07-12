$(document).ready( function() {

    var storages_count = 0;
    var number_of_titles = 0;

    var update_vars = function(url, params, response){
        var number_of_titles_ = 0;
        var storages_count_ = 0;
        var item;
        for (item in response) {
            if (response[item].type == 'storage')
                storages_count_++;
            else
                number_of_titles_++;
        }
        storages_count = storages_count_;
        number_of_titles = number_of_titles_;
        $('#number_of_titles').text(number_of_titles);
        return response
    };

    var group_start_open = function(){
        return (storages_count <= 1);
    };

    var show_tooltips = function(cell) {
        return cell.getRow().getData().path;
    };

    var updated_row = function(row){
        //recalculate movie_counts
    };

    var show_group_header = function(value, count, data){
        //value - the value all members of this group share
        //count - the number of rows in this group
        //data - an array of all the row data objects in this group

        var storage_id = data[0].storage_id;
        //var storage = table.get('storage_id', storage_id);
        //storage.nam, etc...;
        return "Storage " + "<span style='color:#d00; margin-left:10px;'>(" + count + " items)</span>"
            + "<a href=/storage/delete/ class=delete_storage>delete</a>";
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

    $('.delete_storage').click(function(e) {
        return window.confirm("Are you sure to delete that storage?");
    });

    // TODO: check if updating breaks editing. Shouldn't.
    // TODO: Problem: updateOrAdd doesn't delete. But setData def. breaks editing, right?
    var update = function(event){
        $("#storage-tabulator").tabulator("updateOrAddData", "/storage/get_all_storages", {}, "GET");
    };

    $("#storage-tabulator").tabulator({
        ajaxURL: "/storage/get_all_storages",
        ajaxConfig: "GET",
        ajaxResponse: update_vars,

        fitColumns: true,
        movableColumns: true,
        columnVertAlign: "middle",

        groupBy: "storage_id",
        groupHeader: show_group_header,
        groupStartOpen: group_start_open,

        rowUpdated: updated_row,
        cellEdited: modify_movie,

        tooltips: show_tooltips,

        columns: [
            {title: "API", field: "api", minWidth: 80, width:80, editor: true},
            {title: "Scene-ID <br /><span style='fontsize: 8px'>(all?)</span>",
                field: "scene_id", minWidth: 80, width:100, editor: true},
            //{title: "Path", field: "path", visible: false},
            {title: "Title", field: "title", editor: true}
            //{title: "ID", field: "id", visible: false}
        ]

        //TODO: Delete item, from table and from database
        //TODO: Delete/add/modify storage
    })
    .tabulator("setFilter", "type", "!=", 'storage');

});