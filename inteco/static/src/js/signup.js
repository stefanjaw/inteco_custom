odoo.define('inteco.sign_login', (require) => {
    'use strict';

    require('web.dom_ready');
    //alert("Hola mundo");

    if ( $("#login_hide").length > 0 ) {
        validate_company_login();
    }

    if ( $("#text_company_type").length > 0 ) {
        switch_company_type();
    }

    $('#is_company').change(function() {
        validate_company_login();
    });

    function switch_company_type(){
        var company_type = $('#text_company_type').val();
        if (company_type == 'person'){
            $('#is_company').prop('checked', false);
                       $('#name_contact').addClass('show');
                       $('#last_name').addClass('show');
                       $('#second_last_name_contact').addClass('show');
                       $('#company_name').addClass('d-none');
                       $('#name_contact').removeClass('d-none');
                       $('#last_name').removeClass('d-none');
                       $('#second_last_name_contact').removeClass('d-none');
                       $('#company_name').removeClass('show');


                       $('#contact_name').attr("required", true);
                       $('#contact_last_name').attr("required", true);
                       $("#name").attr("required", false);
        }else{
            $('#is_company').prop('checked', true);
                       $('#name_contact').addClass('d-none');
                       $('#last_name').addClass('d-none');
                       $('#second_last_name_contact').addClass('d-none');
                       $('#company_name').addClass('show');
                       $('#name_contact').removeClass('show');
                       $('#last_name').removeClass('show');
                       $('#second_last_name_contact').removeClass('show');
                       $('#company_name').removeClass('d-none');

                       $('#contact_name').attr("required", false);
                       $('#contact_last_name').attr("required", false);
                       $("#name").attr("required", true);
        }
    }


    function validate_company_login(){
       var check = $('input[id="is_company"]:checked').val();
       if (check == 'on'){
           $('#name_contact').addClass('d-none');
           $('#last_name').addClass('d-none');
           $('#second_last_name_contact').addClass('d-none');
           $('#company_name').addClass('show');
           $('#name_contact').removeClass('show');
           $('#last_name').removeClass('show');
           $('#second_last_name_contact').removeClass('show');
           $('#company_name').removeClass('d-none');

           $('#contact_name').attr("required", false);
           $('#contact_last_name').attr("required", false);
           $("#name").attr("required", true);
       }else{
           $('#name_contact').addClass('show');
           $('#last_name').addClass('show');
           $('#second_last_name_contact').addClass('show');
           $('#company_name').addClass('d-none');
           $('#name_contact').removeClass('d-none');
           $('#last_name').removeClass('d-none');
           $('#second_last_name_contact').removeClass('d-none');
           $('#company_name').removeClass('show');


           $('#contact_name').attr("required", true);
           $('#contact_last_name').attr("required", true);
           $("#name").attr("required", false);
       }
    }
});
