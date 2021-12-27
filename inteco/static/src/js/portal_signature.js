/*
    This modification overwrites the submitSign function in order to allow us
    ignoring the customer signature when validating the order from the website.

    Another choice is to create a new controller to handle the accept process
    and then call it directly from the website through a button instead of
    overwriting the JS function. E.g.:
        <form action="/new_controller" method="post">
            <input type='hidden' name='res_id' t-att-value='quotation.id'/>
            ...
            ...
            ...
            <button type="submit">Accept Order</button>
        </form>

    To see the original JS function visit:
    https://github.com/odoo/odoo/blob/11.0/addons/portal/static/src/js/portal_signature.js#L52
*/
odoo.define('inteco.SignatureForm', function(require){
    'use strict';

    require('web_editor.ready');

    var core = require('web.core');
    var rpc = require("web.rpc");

    var qweb = core.qweb;

    var sign_form = require('portal.signature_form');
    sign_form.SignatureForm.include({
        initSign: function () {
            this._super.apply(this, arguments);
            this.$('#o_portal_sign_draw').hide();
        },
        submitSign: function (ev) {
            ev.preventDefault();

            // extract data
            var self = this;
            var $confirm_btn = self.$el.find('button[type="submit"]');

            // process : display errors, or submit
            var partner_name = self.$("#o_portal_sign_name").val();
            var signature = self.$("#o_portal_signature").jSignature('getData', 'image');

            this.$('#o_portal_sign_name').parent().toggleClass('has-error', !partner_name);
            if (! partner_name) {
                return false;
            }

            $confirm_btn.prepend('<i class="fa fa-spinner fa-spin"></i> ');
            $confirm_btn.attr('disabled', true);

            return rpc.query({
                route: this.options.callUrl,
                params: {
                    'res_id': this.options.resId,
                    'access_token': this.options.accessToken,
                    'partner_name': partner_name,
                    'signature': signature ? signature[1] : false,
                },
            }).then(function (data) {
                self.$('.fa-spinner').remove();
                self.$('#o_portal_sign_accept').prepend('<div>PROUT' + data + '</div>');
                if (data.error) {
                    $confirm_btn.attr('disabled', false);
                } else if (data.success) {
                    $confirm_btn.remove();
                    var $success = qweb.render("portal.portal_signature_success", {widget: data});
                    self.$('#o_portal_sign_draw').parent().replaceWith($success);
                }
            });
        },
    });
});

