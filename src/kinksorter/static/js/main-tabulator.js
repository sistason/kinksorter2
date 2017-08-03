var mainstorage_built = false;
var set_mainstorage_header = function(options) {};


var build_mainstorage = function() {
    $("#mainstorage_tabulator").tabulator({
        movableColumns: true,
        fitColumns: true,

        cellEdited: modify_movie,

        tooltips: show_tooltips,

        columns: [
            {title: "", field: 'movie_id', formatter: format_options, minWidth: 50, width: 50,
                formatterParams: {storage_id: 0}, headerSort: false, frozen: true},
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
