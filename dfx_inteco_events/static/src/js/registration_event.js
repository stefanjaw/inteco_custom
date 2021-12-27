odoo.define('dfx_inteco_events.registration_event', function (require) {
    'use strict';
    $(document).ready(function(){

        $("#error_ans").hide();

        function validate_questions(){
            var parent = $( "#questions_select div" ).children();
            var state = 'valid';
            var cont = 0;
//            debugger;
            for (var i=0, max=parent.length; max > i ; i++) {
                if (parent[i].nodeName=="SELECT"){
                    var value = $('option:selected',parent[i]).attr('data-value');
                    debugger;
                    if(value =="True"){
                        $( parent[i] ).parent( "#select_container" ).parent( "#group_questions" ).css({"color": "red"});
                        cont++;
                        $( parent[i] ).siblings().removeClass('d-none');
                    }
                }
            }
            if(cont>0){
                $("#event_continue").prop('disabled', true);
                    state = 'invalid';
                }else{
                    $("#event_continue").prop('disabled', false);
                    state = 'valid';
                }
                return state;
        }


        $('.o_specific_answer').change(function() {
            var value = $('option:selected',this).attr( "data-value");
            var sibling =  $(this).siblings();

            if(value =="True"){
                $("#event_continue").prop('disabled', true);
                sibling.removeClass('d-none');
            }else{
                $( this ).parent( "#select_container" ).parent( "#group_questions" ).css({"color": "black"});
                $("#event_continue").prop('disabled', false);
                sibling.addClass('d-none');
            }
        });

        $("#back_register").click(function(event){
            debugger;
            go_back_register(event);
        });

        function go_back_register () {
            debugger;9
            var route = document.getElementById("route").value;
            var url = '/event/'+route+'/register' ;
            window.location.href = url;
        }

        //Bloqueo de evento del boton para que valide primero las respuestas
        $("#event_continue").click(function(event){
            var val = validate_questions();
            if (val=='invalid'){
                event.preventDefault();
            }
        });

    })
});