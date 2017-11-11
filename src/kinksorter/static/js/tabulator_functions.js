var porn_directory_table_ids = [];
var porn_directory_tabulators = [];
var tables_built = false;

var get_porn_directory_id = function(row){
    var tabulator = row.getElement().closest(".tabulator").get();
    if (!tabulator.length) {
        console.log('Could not find directory-id! row.value: '+row.getValue());
        return -1;
    }

    var $tabulator = tabulator[0];
    return porn_directory_tabulators.findIndex(function($tab_){
        return $tab_ == $tabulator;
    });
};

var show_tooltips = function(cell){
    return cell.getData().full_path;
};
var format_sorted = function(cell) {
    var exists = '<svg enable-background="new 0 0 24 24" height="14" width="14" viewBox="0 0 24 24" xml:space="preserve" ><path fill="#2DC214" clip-rule="evenodd" d="M21.652,3.211c-0.293-0.295-0.77-0.295-1.061,0L9.41,14.34  c-0.293,0.297-0.771,0.297-1.062,0L3.449,9.351C3.304,9.203,3.114,9.13,2.923,9.129C2.73,9.128,2.534,9.201,2.387,9.351  l-2.165,1.946C0.078,11.445,0,11.63,0,11.823c0,0.194,0.078,0.397,0.223,0.544l4.94,5.184c0.292,0.296,0.771,0.776,1.062,1.07  l2.124,2.141c0.292,0.293,0.769,0.293,1.062,0l14.366-14.34c0.293-0.294,0.293-0.777,0-1.071L21.652,3.211z" fill-rule="evenodd"/></svg>',
        link = '<svg enable-background="new 0 0 24 24" height="14" width="14" viewBox="0 0 24 24" xml:space="preserve" ><path fill="yellow" clip-rule="evenodd" d="M21.652,3.211c-0.293-0.295-0.77-0.295-1.061,0L9.41,14.34  c-0.293,0.297-0.771,0.297-1.062,0L3.449,9.351C3.304,9.203,3.114,9.13,2.923,9.129C2.73,9.128,2.534,9.201,2.387,9.351  l-2.165,1.946C0.078,11.445,0,11.63,0,11.823c0,0.194,0.078,0.397,0.223,0.544l4.94,5.184c0.292,0.296,0.771,0.776,1.062,1.07  l2.124,2.141c0.292,0.293,0.769,0.293,1.062,0l14.366-14.34c0.293-0.294,0.293-0.777,0-1.071L21.652,3.211z" fill-rule="evenodd"/></svg>',
        missing = '<svg enable-background="new 0 0 24 24" height="14" width="14"  viewBox="0 0 24 24" xml:space="preserve" ><path fill="#CE1515" d="M22.245,4.015c0.313,0.313,0.313,0.826,0,1.139l-6.276,6.27c-0.313,0.312-0.313,0.826,0,1.14l6.273,6.272  c0.313,0.313,0.313,0.826,0,1.14l-2.285,2.277c-0.314,0.312-0.828,0.312-1.142,0l-6.271-6.271c-0.313-0.313-0.828-0.313-1.141,0  l-6.276,6.267c-0.313,0.313-0.828,0.313-1.141,0l-2.282-2.28c-0.313-0.313-0.313-0.826,0-1.14l6.278-6.269  c0.313-0.312,0.313-0.826,0-1.14L1.709,5.147c-0.314-0.313-0.314-0.827,0-1.14l2.284-2.278C4.308,1.417,4.821,1.417,5.135,1.73  L11.405,8c0.314,0.314,0.828,0.314,1.141,0.001l6.276-6.267c0.312-0.312,0.826-0.312,1.141,0L22.245,4.015z"/></svg>';

    var icon = {'missing': missing, 'link': link, 'exists': exists};
    var state = cell.getData().sorted_state;

    return icon[state];
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
    var porn_directory_id = get_porn_directory_id(cell.getRow());

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

var build_new_porn_directory_container = function() {
    var $new_porn_directory_img = $('<img>', {'class': 'img_functions', 'title': 'Add directory',
        'src': '/static/img/add_porn_directory.png', 'id': 'img_add_directory'})
        .click(add_porn_directory);
    var $new_porn_directory_input_name = $('<input>', {'class': 'input_name', 'name': 'porn_directory_name',
        'placeholder': 'Porn directory name'});
    var $new_porn_directory_input_path = $('<input>', {'class': 'input_path', 'name': 'porn_directory_path',
        'placeholder': 'Porn directory path'});
    var $new_porn_directory_input_ro = $('<input>', {'class': 'input_ro', 'name': 'porn_directory_read_only',
        'type': 'checkbox', 'id': 'cb_input_ro'});
    var $new_porn_directory_label_ro = $('<label>', {'for': 'cb_input_ro'}).text('Read Only?');
    var $new_porn_directory_response = $('<span>', {'id': 'add_porn_directory_response_text'});

    var $new_porn_directory_tr = $('<tr>')
        .append($('<td>').append($new_porn_directory_img))
        .append($('<td>')
            .append($new_porn_directory_input_name)
            .append($new_porn_directory_input_path))
        .append($('<td>')
            .append($new_porn_directory_input_ro)
            .append($new_porn_directory_label_ro));

    var $new_porn_directory_response_tr = $('<tr>', {'class': 'add_porn_directory_response', 'hidden': true})
        .append($('<td>', {'colspan': 3})
            .append($new_porn_directory_response));
    var $new_porn_directory_table =  $('<table>')
        .append($new_porn_directory_tr)
        .append($new_porn_directory_response_tr);

    return $('<div>', {'class': 'porn_directory_0 porn_directory'})
        .append($new_porn_directory_table);
};

var build_porn_directory_function_container = function(porn_directory_id){
    return $('<table>', {'class': 'column_function_container'}).append(
        $('<tr>')
            .append($('<td>', {'class': "rescan_storage"})
                .append($('<div>', {'class': 'click_function'})
                    .click(function() {rescan_porn_directory(porn_directory_id)})
                    .append($('<img>', {'title': 'Rescan storage',
                        'src': '/static/img/rescan_porn_directory.png'}))
                    .append($('<span>', {'class': 'img_description'}).text('Rescan storage'))
                )
            )
            .append($('<td>', {'class': "rescan_porn_directory"})
                .append($('<div>', {'class': 'click_function'})
                    .click(function() {reset_porn_directory(porn_directory_id)})
                    .append($('<img>', {'title': 'Force Rescan storage',
                        'src': '/static/img/force_rescan_porn_directory.png'}))
                    .append($('<span>', {'class': 'img_description'}).text('Reset storage'))
                )
            )
            .append($('<td>', {'class': "recognize_movies"})
                .append($('<div>', {'class': 'click_function'})
                    .click(function() {recognize_porn_directory(porn_directory_id)})
                    .append($('<img>', {'title': 'Recognize unrecognized movies',
                        'src': '/static/img/recognize_porn_directory.png'}))
                    .append($('<span>', {'class': 'img_description'}).text('Recognize unrecognized'))
                )
            )
            .append($('<td>', {'class': "recognize_movies"})
                .append($('<div>', {'class': 'click_function'})
                    .click(function() {recognize_porn_directory(porn_directory_id, true)})
                    .append($('<img>', {'title': 'Force recognize all movies',
                        'src': '/static/img/force_recognize_porn_directory.png'}))
                    .append($('<span>', {'class': 'img_description'}).text('Re-recognize porn_directory'))
                )
            )
        )
};
var build_porn_directory_header_container = function(porn_directory_id){
    return $('<table>', {'class': "column_header_container"}).append(
        $('<tr>')
            .append($('<td>', {'class': "img_add_porn_directory"})
                .append($('<img>', {'title': 'Add all good movies', 'class': 'img_functions',
                    'src': '/static/img/move_to_target.png'})
                    .click(function() {merge_good_movies(porn_directory_id)})
                )
            )
            .append($('<td>', {'class': "column_header"})
                .append($('<span>', {'class': 'porn_directory_name'}).text('_'))
                .append($('<span>', {'class': 'porn_directory_params'}).html('&nbsp;'))
            )
            .append($('<td>', {'class': "img_delete_porn_directory"})
                .append($('<img>', {'title': 'Delete porn_directory', 'class': 'img_functions',
                    'src': '/static/img/delete.png'})
                    .click(function() {delete_porn_directory(porn_directory_id)})
                )
            )
        );
};
var build_porn_directory_container = function(porn_directory_id){
    var base_class = "porn_directory_" + porn_directory_id;
    var $header_container = build_porn_directory_header_container(porn_directory_id);
    var $function_container = build_porn_directory_function_container(porn_directory_id);
    var $tabulator_container = $('<div>', {'id': base_class + '_tabulator'});

    return $('<div>', {'class': base_class + " porn_directory"})
            .append($header_container)
            .append($function_container)
            .append($tabulator_container);
};
var build_porn_directory_tabulator = function(porn_directory_id){
    var $table = $("#porn_directory_" + porn_directory_id + "_tabulator").tabulator({
        height: 800/porn_directory_table_ids.length + "px",

        movableColumns: true,
        fitColumns: true,

        cellEdited: modify_movie,
        rowFormatter: format_row,

        tooltips: show_tooltips,

        columns: [
                {title: "", field: 'movie_id', formatter: format_options, minWidth: 65, width: 65,
                    headerSort: false, frozen: true},
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
        .text(porn_directory_info.porn_directory_path +
            " (" + porn_directory_info.porn_directory_movies_count + " titles)" + read_only);

    $(".porn_directory_" + porn_directory_id + " .column_header").html("Directory ")
        .append($porn_directory_name).append("<br />").append($porn_directory_params);
    $(".porn_directory_" + porn_directory_id + " .column_header .porn_directory_name").blur(function(){
            change_porn_directory_name(porn_directory_id, $(this).text())});
};

var build_target_porn_directory_header_container = function() {
    return $('<table>', {'class': "column_header_container"}).append(
        $('<tr>')
            .append($('<td>', {'class': "img_add_porn_directory"})
                .append($('<img>', {'title': 'Scan for initial movies', 'class': 'img_functions',
                    'src': '/static/img/rescan_porn_directory.png'})
                    .click(function() {scan_target()})
                )
            )
            .append($('<td>', {'class': "column_header"})
                .append($('<span>', {'class': 'porn_directory_name'}).text('Target Directory').append($('<br>')))
                .append($('<span>', {'class': 'porn_directory_params'}).html('&nbsp;'))
            )
            .append($('<td>', {'class': "img_delete_porn_directory"})
                .append($('<img>', {'title': 'Clear target directory', 'class': 'img_functions',
                    'src': '/static/img/delete.png'})
                    .click(clear_target_porn_directory)
                )
            )
        );
};
var build_target_porn_directory_container = function() {
    var $header_container = build_target_porn_directory_header_container();
    var $tabulator_container = $("<div>", {'id': 'target_porn_directory_tabulator'});

    $("#target_porn_directory_container").append($header_container).append($tabulator_container);
};
var build_target_porn_directory_tabulator = function() {
    var $target = $("#target_porn_directory_tabulator").tabulator({
        movableColumns: true,
        fitColumns: true,
        height: "1200px",

        cellEdited: modify_movie,
        rowFormatter: format_row,

        tooltips: show_tooltips,

        columns: [
            {formatter: format_options, minWidth: 48, width: 48, headerSort: false, frozen: true},
            {title: "Sorted", field: 'sorted', formatter: format_sorted, width:40, minWidth:40, frozen: true, align: "center"},
            {title: 'Title', field: "title", formatter: "plaintext", editor: true, frozen: true,
                minWidth: 300, variableHeight: true},
            {title: "ID", field: "scene_id", editor: true, minWidth: 60, width: 60, align: "right"},
            {title: "Date", field: "scene_date", formatter: format_date, minWidth: 95, width: 95},
            {title: "Site", field: "scene_site", width: 150},
            {title: "API", field: "api", minWidth: 80, width: 80},
            {title: "Directory", field: "directory_name", minWidth: 120, width: 120},

            {title: 'Status', field: "status", visible: false},
            {title: 'Movie ID', field: "movie_id", visible: false}
        ]
    });
    porn_directory_tabulators.splice(0, 0, $target.get()[0]);
};
var set_target_porn_directory_header = function(porn_directory_info){
    $("#target_porn_directory_container" + " .porn_directory_params")
        .text(porn_directory_info.porn_directory_path +
            " (" + porn_directory_info.porn_directory_movies_count + " titles)");
};

var build_tables = function() {
    build_target_porn_directory_container();
    build_target_porn_directory_tabulator();

    var $container = $("#porn_directory_tables_container");
    var $new_porn_directory_container = build_new_porn_directory_container();
    $container.append($new_porn_directory_container).append($('<hr>'));

    for (var index in porn_directory_table_ids) {
        var porn_directory_id = porn_directory_table_ids[index];
        var $porn_directory_container = build_porn_directory_container(porn_directory_id);
        $container.append($porn_directory_container).append($('<hr>'));

        build_porn_directory_tabulator(porn_directory_id);
    }
    tables_built = true;
};
