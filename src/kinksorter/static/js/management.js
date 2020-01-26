var build_dragbar = function() {
    var i = 0;
    var dragging = false;
    $('#dragbar').mousedown(function(e){
       e.preventDefault();

       dragging = true;
       var main = $('#porn_directory_tables_container');
       var ghostbar = $('<div>',
                        {id:'ghostbar',
                         css: {
                                height: main.outerHeight(),
                                top: main.offset().top,
                                left: main.offset().left
                               }
                        }).appendTo('body');

        $(document).mousemove(function(e){
          ghostbar.css("left",e.pageX+2);
       });
    });
    $(document).mouseup(function(e){
       if (dragging) {
           var percentage = (e.pageX / window.innerWidth) * 100;
           var mainPercentage = 100-percentage;

           $('#target_porn_directory_container').css("width",(percentage-2) + "%");
           $('#porn_directory_tables_container').css("width",(mainPercentage-2) + "%");
           $('#ghostbar').remove();
           $(document).unbind('mousemove');
           dragging = false;

           // redraw tables to fill now-unused space
           porn_directory_table_ids.forEach(function(i){
               $("#porn_directory_"+i+"_tabulator").tabulator("redraw");
           });
           $("#target_porn_directory_tabulator").tabulator("redraw");
       }
    });
};

$(document).ready(function(){
    setup();
    build_target_porn_directory_tabulator();

    update_tables();

    setInterval(update_current_task, 1000);
    update_tables_timer_id = setInterval(update_tables, 10000);

    build_dragbar();

    $('.delete').click(function(e) {
        return window.confirm("Are you sure to delete that?");
    }); //TODO: not working

});
