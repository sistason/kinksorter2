var porn_directory_table_ids = [];
var porn_directory_tabulators = [];
var tables_built = false;

var get_porn_directory_id = function(cell_row){
    var tabulator = cell_row.getElement().closest(".tabulator").get();
    if (!tabulator.length)
        return -1;

    var $tabulator = tabulator[0];
    return porn_directory_tabulators.findIndex(function($tab_){
        return $tab_ == $tabulator;
    });
};

var show_tooltips = function(cell){
        return cell.getData().full_path;
};
var format_row = function(row){
    var color = {'unrecognized': '#ffc0c0', 'duplicate': '#ffffc0', 'okay': '#c0ffc0'};

    var status = row.getData().status;

    if (get_porn_directory_id(row) == 0 && status == 'duplicate')
        status = 'okay';

    row.getElement().css({"background-color": color[status]});
};
var format_date = function(cell){
    var ts = parseInt(cell.getValue()) || null;
    if (ts == null)
        return;

    var date = new Date(ts*1000);
    return date.toISOString().slice(0,10);
};
var format_options = function(cell){
    var status = cell.getData().status;
    var porn_directory_id = get_porn_directory_id(cell);

    var $container = $('<div>', {'class': 'options_container'});

    var $del = $('<img>');
    if (porn_directory_id != 0){
        $del.attr({alt: "Delete", src: '/static/img/delete.png', 'class': 'img_options delete'});
        $del.click(function(){
            delete_movie(cell.getRow())
        });

        if (status != 'duplicate' && ! cell.getData().in_target) {
            var src = (status == 'okay') ? '/static/img/move_to_target.png' : '/static/img/move_unrecognized_to_target.png';
            var $add = $('<img>', {alt: "Add", src: src, 'class': 'img_options'});
            $add.click(function(){
                move_movie_to_target(cell.getRow())
            });
            $container.append($add).append('&nbsp;');
        }

    }
    else {
        $del.attr({alt: "Remove", src: '/static/img/remove_from_target.png', 'class': 'img_options'});
        $del.click(function(){remove_movie_from_target(cell.getRow())});
    }

    var $watch = $('<img>', {alt: "Watch", src: '/static/img/watch.png', 'class': 'img_options'});
    $watch.click(function(){
        window.open('/play_video/'+cell.getData().movie_id, '_blank');
    });

    $container.append($del);
    $container.append('&nbsp;');
    $container.append($watch);

    return $container;
};

var build_porn_directory_container = function(porn_directory_id){
    var base_class = "porn_directory_" + porn_directory_id;
    // TODO: jqueryize
    $("#porn_directory_tables_container").append(
        "<div class='"+base_class+" porn_directory'>" +
            "<table class='column_header_container'>" +
                "<tr>" +
                    "<td class='img_add_porn_directory'>" +
                        "<img title='Add all good movies' class='img_functions' " +
                            "src='/static/img/move_to_target.png' onClick='merge_good_movies(" + porn_directory_id + ")' />" +
                    "</td>" +
                    "<td class='column_header'>" +
                        "<span class='porn_directory_name'>_</span>" +
                        "<br /><span class='porn_directory_params'>&nbsp;</span>" +
                    "</td>" +
                    "<td class='img_delete_porn_directory'>" +
                        "<img title='Delete porn_directory' class='img_functions' src='/static/img/delete.png' "+
                            "onClick='delete_porn_directory(" + porn_directory_id + ")' />" +
                    "</td>" +
                "</tr>"+
            "</table>" +
            "<table class='column_function_container'>" +
                "<tr>" +
                    "<td class='rescan_storage'>" +
                        //TODO: Mouseover: verbose explanation
                        "<div class='click_function' onClick='rescan_porn_directory(" + porn_directory_id + ")'>" +
                            "<img title='Rescan storage' src='/static/img/rescan_porn_directory.png'  />" +
                            "<span class=img_description>Rescan storage</span>"+
                        "</div>" +
                    "</td>" +
                    "<td class='rescan_porn_directory'>" +
                        "<div class='click_function' onClick='reset_porn_directory(" + porn_directory_id + ")'>" +
                            "<img title='Force Rescan storage' src='/static/img/force_rescan_porn_directory.png' />" +
                            "<span class=img_description>Reset storage</span>"+
                        "</div>" +
                    "</td>" +
                    "<td class='recognize_movies'>" +
                        "<div class='click_function' onClick='recognize_porn_directory(" + porn_directory_id + ")'>" +
                            "<img title='Recognize unrecognized movies' src='/static/img/recognize_porn_directory.png' />" +
                            "<span class=img_description>Recognize unrecognized</span>" +
                        "</div>" +
                    "</td>" +
                    "<td class='recognize_movies'>" +
                        "<div class='click_function' onClick='recognize_porn_directory(" + porn_directory_id + ", true)'>" +
                            "<img title='Force recognize all movies' src='/static/img/force_recognize_porn_directory.png' />" +
                            "<span class=img_description>Re-recognize porn_directory</span>" +
                        "</div>" +
                    "</td>" +
                "</tr></table>" +
            "<div id='"+base_class+"_tabulator'></div>" +
        "<hr />" +
        "</div>"
        );
};
var build_porn_directory_tabulator = function(porn_directory_id){
    var $table = $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator({
        //height:"100%",

        movableColumns: true,
        fitColumns: true,

        cellEdited: modify_movie,
        rowFormatter: format_row,

        tooltips: show_tooltips,

        columns: [
                {title: "", field: 'movie_id', formatter: format_options, minWidth: 65, width: 65,
                    formatterParams: {porn_directory_id: porn_directory_id}, headerSort: false, frozen: true},
                {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                    minWidth: 300, variableHeight: true},
                {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
                {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
                {title: "Site", field: "scene_site", width: 150},
                {title: "API", field: "api", minWidth: 80, width: 80}
        ]
    });
    porn_directory_tabulators.splice(porn_directory_id, 0, $table.get()[0]);
};
var set_porn_directory_header = function(porn_directory_info, porn_directory_id){
    var $porn_directory_name = $('<span>', {'class': 'porn_directory_name'})
        .text(porn_directory_info.porn_directory_name).prop('contentEditable', true);
    var read_only = ((porn_directory_info.porn_directory_read_only) ? " [read_only]" : "");
    var $porn_directory_params = $('<span>', {'class': 'porn_directory_params'})
        .text("(" + porn_directory_info.porn_directory_movies_count + " titles)" + read_only);

    $(".porn_directory_" + porn_directory_id + " .column_header").html("Directory ")
        .append($porn_directory_name).append("<br />").append($porn_directory_params);
    $(".porn_directory_" + porn_directory_id + " .column_header .porn_directory_name").blur(function(){
            change_porn_directory_name(porn_directory_id, $(this).text())});
};

var build_target_porn_directory_tabulator = function() {
    var $target = $("#target_porn_directory_tabulator").tabulator({
        movableColumns: true,
        fitColumns: true,

        cellEdited: modify_movie,
        rowFormatter: format_row,

        tooltips: show_tooltips,

        columns: [
            {title: "", field: 'movie_id', formatter: format_options, minWidth: 48, width: 48,
                formatterParams: {porn_directory_id: 0}, headerSort: false, frozen: true},
            {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                minWidth: 300, variableHeight: true},
            {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60},
            {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
            {title: "Site", field: "scene_site", width: 150},
            {title: "API", field: "api", minWidth: 80, width: 80},
            {title: "Directory", field: "porn_directory_name", minWidth: 100, width: 100},

            {title: 'Status', field: "status", visible: false},
            {title: 'Movie ID', field: "movie_id", visible: false}
        ]
    });
    porn_directory_tabulators.splice(0, 0, $target.get()[0]);
};
var set_target_porn_directory_header = function(options) {};

var build_tables = function() {
    build_target_porn_directory_tabulator();
    for (var index in porn_directory_table_ids) {
        var porn_directory_id = porn_directory_table_ids[index];
        build_porn_directory_container(porn_directory_id);
        build_porn_directory_tabulator(porn_directory_id);
    }
    tables_built = true;
};
