/*
    This was copied from:
    https://github.com/odoo/odoo/blob/a89e46fd/addons/mail/static/src/js/chatter_composer.js
    only the context generation was modified
    We know copying an entire script to modify only two lines is not ideal, but
    the way the original script is defined leaved us with no choice
    For more information about what changes were made, see:
    https://github.com/odoo/odoo/pull/24930
    TODO remove this file after the above PR is merged, or
    remove this TODO if it's closed
*/
/* eslint-disable */
odoo.define('inteco.ChatterComposer', function(require){
    'use strict';

    var core = require('web.core');
    var view_dialogs = require('web.view_dialogs');
    var utils = require('mail.utils');
    var _t = core._t;
    var chatter = require('mail.ChatterComposer');

    chatter.include({
        check_suggested_partners: function (checked_suggested_partners) {
            var self = this;
            var check_done = $.Deferred();

            var recipients = _.filter(checked_suggested_partners, function (recipient) { return recipient.checked; });
            var recipients_to_find = _.filter(recipients, function (recipient) { return (! recipient.partner_id); });
            var names_to_find = _.pluck(recipients_to_find, 'full_name');
            var recipients_to_check = _.filter(recipients, function (recipient) { return (recipient.partner_id && ! recipient.email_address); });
            var recipient_ids = _.pluck(_.filter(recipients, function (recipient) { return recipient.partner_id && recipient.email_address; }), 'partner_id');

            var names_to_remove = [];
            var recipient_ids_to_remove = [];

            // have unknown names -> call message_get_partner_info_from_emails to try to find partner_id
            var def;
            if (names_to_find.length > 0) {
                def = this._rpc({
                        model: this.model,
                        method: 'message_partner_info_from_emails',
                        args: [[this.context.default_res_id], names_to_find],
                    });
            }

            // for unknown names + incomplete partners -> open popup - cancel = remove from recipients
            $.when(def).pipe(function (result) {
                result = result || [];
                var emails_deferred = [];
                var recipient_popups = result.concat(recipients_to_check);

                _.each(recipient_popups, function (partner_info) {
                    var deferred = $.Deferred();
                    emails_deferred.push(deferred);

                    var partner_name = partner_info.full_name;
                    var partner_id = partner_info.partner_id;
                    var parsed_email = utils.parse_email(partner_name);

                    var dialog = new view_dialogs.FormViewDialog(self, {
                        res_model: 'res.partner',
                        res_id: partner_id,
                        context: _.assign({
                            force_email: true,
                            ref: "compound_context",
                            default_name: parsed_email[0],
                            default_email: parsed_email[1],
                        }, partner_info['context'] || {}),
                        title: _t("Please complete customer's informations"),
                        disable_multiple_selection: true,
                    }).open();
                    dialog.on('closed', self, function () {
                        deferred.resolve();
                    });
                    dialog.opened().then(function () {
                        dialog.form_view.on('on_button_cancel', self, function () {
                            names_to_remove.push(partner_name);
                            if (partner_id) {
                                recipient_ids_to_remove.push(partner_id);
                            }
                        });
                    });
                });
                $.when.apply($, emails_deferred).then(function () {
                    var new_names_to_find = _.difference(names_to_find, names_to_remove);
                    var def;
                    if (new_names_to_find.length > 0) {
                        def = self._rpc({
                                model: self.model,
                                method: 'message_partner_info_from_emails',
                                args: [[self.context.default_res_id], new_names_to_find, true],
                            });
                    }
                    $.when(def).pipe(function (result) {
                        result = result || [];
                        var recipient_popups = result.concat(recipients_to_check);
                        _.each(recipient_popups, function (partner_info) {
                            if (partner_info.partner_id && _.indexOf(partner_info.partner_id, recipient_ids_to_remove) === -1) {
                                recipient_ids.push(partner_info.partner_id);
                            }
                        });
                    }).pipe(function () {
                        check_done.resolve(recipient_ids);
                    });
                });
            });
            return check_done;
        },
    });
});
/* eslint-enable */
