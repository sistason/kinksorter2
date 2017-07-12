$(document).ready( function() {

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

    $('.confirm').click(function(e) {
        return window.confirm("Are you sure to delete that storage?");
    });

    var update = function(event){
        $("#storage-tabulator").tabulator("updateOrAddData", "/storage/get_all_storages", {}, "GET");
    };


    $("#storage-tabulator").tabulator({
        ajaxURL: "/storage/get_all_storages",
        ajaxConfig: "GET",
        /*ajaxResponse: function(url, params, response){
            //url - the URL of the request
            //params - the parameters passed with the request
            //response - the JSON object returned in the body of the response.

            return response.tableData; //return the tableData peroperty of a response json object
        },*/

        //height: "311px",
        fitColumns: false,
        responsiveLayout: true,
        groupBy: "storage_id",
        groupHeader:function(value, count, data){
            //value - the value all members of this group share
            //count - the number of rows in this group
            //data - an array of all the row data objects in this group

            var storage = $("#example-table").tabulator("getRow", 1);
            //var storage = table.get('storage_id': data);
            //storage.nam, etc...;
            return "Storage " + "<span style='color:#d00; margin-left:10px;'>(" + count + " items)</span>";
        },
        rowUpdated: function(row){
            //recalculate movie_counts
        },
        cellEdited: modify_movie,
        tooltips:function(cell) {
            return cell.getRow().getData().path;
        },

        columns: [
            {title: "API", field: "api", width: 60, editor: true},
            {title: "Scene-ID (show already recognized?)", field: "scene_id", width: 30, editor: true},
            //{title: "Path", field: "path", visible: false},
            {title: "Title", field: "title", editor: true}
            //{title: "ID", field: "id", visible: false}
        ]
    })
    .tabulator("setFilter", "type", "!=", 'storage');



});