odoo.define('inteco.contactus', function(require){
    'use strict';

    var ajax = require('web.ajax');
    require('web.dom_ready');

    $("#subservice_div").hide();
    $('.form-field').on("change", 'select[name="team_id"]',
        function () {
            var team_id = $("#team_id :selected").val();
            if (team_id) {
                ajax.jsonRpc("/contactus/subservices", 'call',
                    {team_id: Number(team_id)}).then(function (data) {
                        var selectSubservices = $("#subservices");
                        if(data.subserv.length) {
                            selectSubservices.html('');
                            _.each(data.subserv, function(x) {
                                var opt = $('<option>').text(x[1])
                                    .attr('value', x[0]);
                                selectSubservices.append(opt);
                            });
                            $("#subservice_div").show();
                        } else {
                           $("#subservice_div").hide();
                        }
                    });
            }
    });
});

// Allows to redirect when the user selects a category in the products catalog
odoo.define('inteco.catalog', function(require){
    'use strict';

    require('web.dom_ready');

    $('#category').on('change', function () {
        var url = $(this).val();
        if (url) {
            window.location = url;
        }
    });
});

// Enables an additional field to be filled as a complement of the description
// field when the selected type is 'Complaint'.
odoo.define('inteco.complaints', function(require){
    'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');

    $('#ticket_type_id').on('change', function () {
        var ticket_type = $("#ticket_type_id option:selected").val();
        ajax.jsonRpc("/helpdesk/complaint-form", 'call',
            {form_type_id: Number(ticket_type)}
        ).then(function (data) {
            if(data) {
                $('#complaint_field').css('display','block');
            } else {
                $('#complaint_field').css('display','none');
            }
        });
    });
});
