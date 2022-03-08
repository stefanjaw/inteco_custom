# -*- coding: utf-8 -*-
import re
import logging
import threading

from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.tools.misc import split_every
from odoo.exceptions import ValidationError, UserError


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'phone.validation.mixin']

    legal_name = fields.Char(
        string="Social Reason",
        help="Official name of the company, it must be the same name as it "
        "appears in the legal documentation."
    )
    contact_name = fields.Char(
        string="Names",
        help="This field is mandatory because is used to compute the name of "
        "the partner when the company type is individual.",
    )
    contact_last_name = fields.Char(
        string="Last Names",
        help="This field is mandatory because is used to compute the name of "
        "the partner when the company type is individual.",
    )
    second_last_name = fields.Char(
        help="This field is joined to the partner name when it's provided."
    )

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self.phone_format(self.phone, raise_exception=True)

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self.phone_format(self.mobile, raise_exception=True)

    def _check_email_duplicated(self):
	return
        """Ensures that the email address is unique for each contact. We
        decided to use an onchange instead of a constraint due to there are
        a lot of previously registered emails."""
        # I prefer to use "- self" to avoid the current line
        # because if I add the tuple ('id', '!=', self.id),
        # when the partner is a new partner can occurs
        # the following error:
        # ProgrammingError: can't adapt type 'NewId'
        # because line.id will be
        # <odoo.models.NewId object at 0x7f6a47fd9750>
        partner = self.sudo().search([
            ('email', '=', self.email)]) - self \
            if self.email else False
        if partner:
            raise ValidationError(
                _(
                    'Take into account that the following contact already'
                    'has the same email registered: \n\n- %s <%s>') % (
                        partner.display_name, partner.email))

    @api.constrains('email')
    def _check_email(self):
		return
        """Even when the email field is validated using the email_validator
        widget in the front-end it is convenient also to add a constraint for
        those cases when the information is not entered directly from the
        contact form like the case of a contact importation."""
        pattern = (
            r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|'
            r'(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]'
            r'{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
        )
        for record in self:
            if record.email:
                record._check_email_duplicated()
            if not record.email and record.company_type == 'person':
                raise ValidationError(
                    _('The email is required for individual \n'))
            if record.email and not re.match(pattern, record.email.lower()):
                raise ValidationError(
                    _("The format of the email is incorrect.")
                )

    @api.onchange('contact_name', 'contact_last_name', 'second_last_name',
                  'is_company')
    def _onchange_full_name(self):
        """This method is used to fill automatically the partner name with a
        combination of contact information fields."""
        if self.contact_name:
            self.contact_name = self.contact_name.title()
        if self.contact_last_name:
            self.contact_last_name = self.contact_last_name.title()
        if self.second_last_name:
            self.second_last_name = self.second_last_name.title()
        full_name = ' '.join([n for n in [
            self.contact_name, self.contact_last_name, self.second_last_name
        ] if n])
        if not self.is_company:
            self.name = full_name

    @api.model
    def _notify(self, message, rdata, record, force_send=False, send_after_commit=True, model_description=False,
                mail_auto_delete=True):
        """ Method to send email linked to notified messages. The recipients are
        the recordset on which this method is called.

        :param message: mail.message record to notify;
        :param rdata: recipient data (see mail.message _notify);
        :param record: optional record on which the message was posted;
        :param force_send: tells whether to send notification emails within the
          current transaction or to use the email queue;
        :param send_after_commit: if force_send, tells whether to send emails after
          the transaction has been committed using a post-commit hook;
        :param model_description: optional data used in notification process (see
          notification templates);
        :param mail_auto_delete: delete notification emails once sent;
        """
        if not rdata:
            return True

        base_template_ctx = self._notify_prepare_template_context(message, record, model_description=model_description)
        template_xmlid = 'mail.message_notification_email'
        try:
            base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(
                lang=base_template_ctx['lang'])
        except ValueError:
            _logger.warning(
                'QWeb template %s not found when sending notification emails. Sending without layouting.' % (
                    template_xmlid))
            base_template = False

        # prepare notification mail values
        base_mail_values = {
            'mail_message_id': message.id,
            'mail_server_id': message.mail_server_id.id,
            'auto_delete': mail_auto_delete,
            'references': message.parent_id.message_id if message.parent_id else False
        }
        if record:
            base_mail_values.update(
                self.env['mail.thread']._notify_specific_email_values_on_records(message, records=record))

        # classify recipients: actions / no action
        recipients = self.env['mail.thread']._notify_classify_recipients_on_records(message, rdata, records=record)

        Mail = self.env['mail.mail'].sudo()
        emails = self.env['mail.mail'].sudo()
        email_pids = set()
        recipients_nbr, recipients_max = 0, 50
        for group_tpl_values in [group for group in recipients.values() if group['recipients']]:
            # generate notification email content
            template_ctx = {**base_template_ctx, **group_tpl_values}
            mail_body = base_template.render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
            mail_body = self.env['mail.thread']._replace_local_links(mail_body)
            mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name)

            # send email
            for email_chunk in split_every(50, group_tpl_values['recipients']):
                recipient_values = self.env['mail.thread']._notify_email_recipients_on_records(message, email_chunk,
                                                                                               records=record)
                create_values = {
                    'body_html': mail_body,
                    'subject': mail_subject,
                }
                create_values.update(base_mail_values)
                create_values.update(recipient_values)
                recipient_ids = [r[1] for r in create_values.get('recipient_ids', [])]
                email = Mail.create(create_values)

                if email and recipient_ids:
                    notifications = self.env['mail.notification'].sudo().search([
                        ('mail_message_id', '=', email.mail_message_id.id),
                        ('res_partner_id', 'in', list(recipient_ids))
                    ])
                    notifications.write({
                        'is_email': True,
                        'mail_id': email.id,
                        'is_read': True,  # handle by email discards Inbox notification
                        'email_status': 'ready',
                    })

                emails |= email
                email_pids.update(recipient_ids)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.currentThread(), 'testing', False)
        if force_send and len(emails) < recipients_max and \
                (not self.pool._init or test_mode):
            email_ids = emails.ids
            dbname = self.env.cr.dbname
            _context = self._context

            def send_notifications():
                db_registry = registry(dbname)
                with api.Environment.manage(), db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, _context)
                    env['mail.mail'].browse(email_ids).send()

            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                self._cr.after('commit', send_notifications)
            else:
                emails.send()

        return True

    # @api.multi
    # def _notify(self, message, rdata, record, force_send=False, send_after_commit=True, model_description=False, mail_auto_delete=True):
	#     template = 'inteco.mail_template_data_notification_email_default'
	#     self.with_context(custom_layout=template)
	#     return super(ResPartner, self)._notify(message, rdata, record, force_send=force_send, send_after_commit=send_after_commit, model_description=model_description, mail_auto_delete=mail_auto_delete)

    def export_data(self, fields_to_export):
        """Don't allow to export data if the user doesn't belon to the group
            'Export Data'
        """
        if not self.env.user.has_group('inteco.group_export_data'):
            raise UserError(_(
                'Only users from the group "Exporting Permissions" may '
                'export data.'))
        return super(ResPartner, self).export_data(fields_to_export)

    @api.model
    def split_full_name(self, full_name):
        """ Given a person's full name, split it into a name, last name and a
            second last name. This behaves as follows:
            - 1 word   -> 1 name
            - 2 words  -> 1 name, 1 lastname
            - 3 words  -> 1 name, 2 lastnames
            - 4 words  -> 2 names, 2 lastnames
            - 5+ words -> 3+ names, 2 lastnames
        """
        if not full_name:
            return (full_name, False, False)
        names = full_name.split()
        num_names = len(names)
        first_name = last_name = second_last_name = False

        if num_names <= 2:
            first_name = names[0]
            last_name = names[1] if num_names == 2 else False
        else:
            first_name = ' '.join(names[:-2])
            last_name = names[-2]
            second_last_name = names[-1]
        return (first_name, last_name, second_last_name)

    @api.model
    def name_create(self, name):
        """ If the partner is being created from a lead, creates it setting its
            fields from the lead, instead of filling only the name and email
        """
        if self._context.get('active_model') == 'crm.lead':
            lead = self.env['crm.lead'].browse(self._context.get('active_id'))
            partner = lead._create_lead_partner()
            return partner.name_get()[0]
        return super(ResPartner, self).name_create(name)

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                         submenu=False):
        """ When a partner is created from the lead's chatter, uses a
            customized view capable of displaying all partner fields coming
            from the lead
        """
        if (not view_id and view_type == 'form'
                and self._context.get('src_model') == 'crm.lead'
                and self._context.get('ref') == 'compound_context'):
            view_id = self.env.ref('inteco.view_partner_simple_form_lead').id
        return super(ResPartner, self)._fields_view_get(
            view_id, view_type, toolbar, submenu)

    @api.model
    def create(self, vals):
        """ If the partner is created without neither name, lastname nor second
            last name (e.g. when created from a sign up), fill those fields
            parsing them from the partner name
        """
        if (vals.get('name') and not vals.get('is_company')
                and not vals.get('contact_name')
                and not vals.get('contact_last_name')
                and not vals.get('second_last_name')):
            first_name, last_name, second_last_name = self.split_full_name(
                vals.get('name'))
            vals.update({
                'contact_name': first_name,
                'contact_last_name': last_name,
                'second_last_name': second_last_name,
            })
        return super(ResPartner, self).create(vals)

    def is_valid_name(self, name):
        return
        """ Given a person's name, returns whether the name is an allowed one
        """
        if re.search(r'\d', name):
            # Name contains numbers
            return False
        return True

    @api.constrains('name', 'is_company')
    def _check_full_name(self):
        return
        """ Raises an exception if the person's name is not valid
        """
        if not self.is_company and not self.is_valid_name(self.name):
            raise ValidationError(_(
                "The name may not contain numbers. Please, try again."))
