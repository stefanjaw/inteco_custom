odoo.define('inteco.tour', function(require) {
    'use strict';

    var tour = require('web_tour.tour');
    var base = require('web_editor.base');

    tour.register('inteco_request_quotation_tour', {
        test: true,
        url: '/',
        wait_for: base.ready(),
    }, [{
        content: "Click on 'Solicitar cotización'",
        trigger: "a[href='/contactus?alias=cotizacion']",
    }, {
        content: "Complete request type: select 'Solicitud de Cotización'",
        trigger: "select[name=type_of_request]",
        run: "text request",
    }, {
        content: "Complete team: select 'General'",
        trigger: "select[name=team_id]",
        run: "text 6",
    }, {
        content: "Complete subservice: select 'ISO 9001'",
        trigger: "select[name=subservices]",
        run: "text 7",
    }, {
        content: "Complete first name",
        trigger: "input[name=first_name]",
        run: "text John",
    }, {
        content: "Complete first last name",
        trigger: "input[name=last_name]",
        run: "text Doe",
    }, {
        content: "Complete second last name",
        trigger: "input[name=second_last_name]",
        run: "text Lee",
    }, {
        content: "Complete country",
        trigger: "select[name=country_id]",
        run: "text 50",

    },{
        content: "Complete phone number",
        trigger: "input[name=phone]",
        run: "text +50622834522"
    }, {
        content: "Complete Email",
        trigger: "input[name=email_from]",
        run: "text john.doe@example.com"
    }, {
        content: "Complete Company",
        trigger: "input[name=partner_name]",
        run: "text Odoo S.A."
    }, {
        content: "Complete Subject",
        trigger: "input[name=name]",
        run: "text Quotation request"
    }, {
        content: "Complete Description",
        trigger: "textarea[name=description]",
        run: "text I'd like to request a quotation"
    }, {
        content: "Send the form",
        trigger: ".o_website_form_send"
    }, {
        content: "Check we were redirected to the success page",
        trigger: "#wrap:has(h1:contains('Gracias')):has(div.alert-success)"
    }]);

    return {};
});
