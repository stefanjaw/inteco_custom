# -*- coding: utf-8 -*-

import re
from datetime import date, timedelta
from email.utils import parseaddr

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.fields import Date


class Lead(models.Model):
    _inherit = 'crm.lead'

    assigned_activity = fields.Boolean(
        copy=False,
        default=False,
        help="Indicates if the default activities for the current stage were "
             "already assigned."
    )
    first_name = fields.Char(string="Names", help="This field is mandatory\
                             because is used to compute the contact's name")
    last_name = fields.Char(string="Last Names", help="This field is mandatory\
                            because is used to compute the contact's name")
    second_last_name = fields.Char(
        help="This field is joined to the contact name when it's provided."
    )
    lost_company_name = fields.Char(
        string="Competitor's company name",
        help="Company against which the opportunity was lost"
    )
    subservice_id = fields.Many2one(
        'crm.subservice', string='Subservice',
        help="Subservice associated with the lead/opportunity"
    )

    def _default_stage_id(self):
        team = self.env['crm.team'].sudo()._get_default_team_id(user_id=self.env.uid)
        return self._stage_find(team_id=team.id, domain=[('fold', '=', False)]).id

    #TODO QUITAR @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        res = super(Lead, self)._create_lead_partner_data(
            name, is_company, parent_id)
        if res.get('is_company'):
            res['email'] = False
        else:
            res.update({
                'contact_name': self.first_name,
                'contact_last_name': self.last_name,
                'second_last_name': self.second_last_name,
            })
        return res

    def website_form_input_filter(self, request, values):
        super(Lead, self).website_form_input_filter(request, values)
        new_values = {}
        name = request.params.get('first_name').title()
        last_name_one = request.params.get('last_name').title()
        last_name_two = request.params.get('second_last_name')
        country_id = int(request.params.get('country_id')) or False
        subservice_id = request.params.get('subservices') or False
        if last_name_two:
            last_name_two = last_name_two.title()
            new_values.update({'second_last_name': last_name_two})
        complete_name = ' '.join(
            [n for n in [name, last_name_one, last_name_two] if n])

        # Retrieves default values from parameters
        get_param = request.env['ir.config_parameter'].sudo().get_param
        campaign_id = int(get_param('lead_website_campaign')) or False
        medium_id = int(get_param('lead_website_medium')) or request.params.get('medium_id') or int(1) or False
        source_id = int(get_param('lead_website_source')) or False

        new_values.update({
            'first_name': name,
            'last_name': last_name_one,
            'contact_name': complete_name,
            'campaign_id': campaign_id,
            'medium_id': medium_id,
            'source_id': source_id,
            'country_id': country_id,
            'subservice_id': subservice_id,
        })

        type_of_request = {
            'request': _('Request for Quotation'),
            'consult': _('General Consult'),
            'cso': _(''),
            'bcp': _('')
        }

        company = request.params.get('partner_name') or False
        email_form = request.params.get('email_from')
        partner_form = self.env['res.partner'].search([('name', '=', company)], limit=1, order='id asc')
        partner_email_form = self.env['res.partner'].search([('email', '=', email_form)], limit=1, order='id asc')

        partner_vals = {
            'name': complete_name,
            'company_type': 'person',
            'contact_name': name,
            'contact_last_name': last_name_one or False,
            'second_last_name': last_name_two or False,
            'email': email_form,
            'country_id': country_id,
            'phone': request.params.get('phone') or False,
        }

        if partner_email_form:
            new_values.update({'partner_id': partner_email_form.id})
            if partner_email_form.category_id:
                new_values.update({'contact_tags': [(6, 0, partner_email_form.category_id.ids)]})
            else:
                new_values.update({'contact_tags': [(4, 48)]})
        else:
            if partner_form:
                partner_vals.update({'parent_id': partner_form.id})
                new_partner = self.env['res.partner'].sudo().create(partner_vals)
                new_values.update({'partner_id': new_partner.id})
                new_values.update({'contact_tags': [(4, 48)]})
            else:
                new_company = self.env['res.partner'].sudo().create({
                    'company_type': 'company',
                    'name': company
                })
                partner_vals.update({'parent_id': new_company.id})
                new_partner = self.env['res.partner'].sudo().create(partner_vals)
                new_values.update({'partner_id': new_partner.id})
                new_values.update({'contact_tags': [(4, 48)]})

        text_typereq = type_of_request[request.params.get(
            'type_of_request')] or ''
        subject = request.params.get('name') or ''
        subservice = request.env['crm.subservice'].search([
            ('id', '=', subservice_id)
        ])
        if medium_id == '12':
            new_values.update({
                'name': subject
            })
        else:
            if medium_id == '13':
                new_values.update({
                    'name': subject
                })
            else:
                new_values.update({
                    'name': ' - '.join(
                        x for x in (text_typereq, subservice.name, subject) if x)
                })

        if subservice.responsible_id:
            new_values.update({'user_id': subservice.responsible_id.id})
        values.update(new_values)

        return values

    #TODO QUITAR @api.multi
    def new_automatic_activity(self, activities):
        """Schedules the default activities for the stage."""
        self.ensure_one()
        for activity in activities:
            self.env['mail.activity'].create({
                'activity_type_id': activity.id,
                'summary': activity.name,
                'date_deadline': self.date_after_wo_weekends(
                    Date.today(), activity.days),
                'user_id': self.env.user.id,
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': self.id,
            })
        self.assigned_activity = True
        return True

    @api.model
    def date_after_wo_weekends(self, start_date, days):
        """Given a date and a number of working days, returns the effective
            date in which a task would be completed, excluding weekends
        """
        if isinstance(start_date, str):
            start_date = Date.from_string(start_date)
        start_weekday = start_date.weekday()
        worked_days = 0
        position = 0
        weekend_days = 0
        while worked_days < days:
            position += 1
            position_weekday = (start_weekday + position) % 7
            if position_weekday > 4:  # weekend
                weekend_days += 1
            else:
                worked_days += 1
        return start_date + timedelta(days=days + weekend_days)

    @api.constrains('stage_id')
    def stage_change(self):
        """Checks if there are activities to be done before changing stage."""

        if self.stage_id.id == self.env['crm.lead']._default_stage_id():
            return True

        if self.team_id != self.stage_id.team_id:
            raise ValidationError(
                _("This stage is not related with the %s team.") % (
                    self.team_id.name)
            )

        if not self.activity_ids:
            self.assigned_activity = False
            return True

        raise ValidationError(
            _("You can not change the stage until the following activities "
              "are marked as done: \n %s") % (
                '\n'.join(self.activity_ids.mapped('summary')))
        )

    @api.onchange('date_deadline')
    def _onchange_date_deadline(self):
        if self.date_deadline and \
                fields.Date.from_string(self.date_deadline) < date.today():
            raise ValidationError(
                _("The expected closing date cannot be lower than the "
                  "current date.")
            )

    @api.constrains('email_from')
    def _check_email(self):
        """Even when the email field is validated using the email_validator
        widget in the front-end it is convenient also to add a constraint for
        those cases when the information is not entered directly from the
        contact form like the case of a contact importation."""
        pattern = (
            r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|'
            r'(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]'
            r'{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
        )
        for record in self.filtered('email_from'):
            if not re.match(pattern, record.email_from.lower()):
                raise ValidationError(
                    _("The format of the email is incorrect.")
                )

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self.phone_format(self.phone, raise_exception=True)

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self.phone_format(self.mobile, raise_exception=True)

    #TODO QUITAR @api.multi
    def lead_to_opportunity(self):
        """Before converting a lead into an opportunity it's necessary to
        verify that at least the basic information about the contact was
        provided."""
        warnings = [
            (not self.contact_name, _("Specify Contact name.")),
            (not self.email_from, _("Specify Email.")),
            (not self.country_id, _("Specify Country.")),
        ]
        messages = [msg for value, msg in warnings if value]

        if not messages:
            action = self.env.ref(
                'crm.action_crm_lead2opportunity_partner').read()[0]
            return action

        raise ValidationError(
            _("To convert to an opportunity you must meet the following "
              "requirements: \n- %s") % ('\n- '.join(messages)))

    #TODO QUITAR @api.multi
    def write(self, vals):
        team_id = vals.get('team_id')
        if team_id:
            self.activity_ids.unlink()
            new_stage = self.env['crm.lead']._stage_find(
                team_id=team_id, domain=[('fold', '=', False)])
            vals.update({
                'stage_id': new_stage.id,
                'assigned_activity': False,
            })
        return super(Lead, self).write(vals)

    @api.onchange('first_name', 'last_name', 'second_last_name')
    def _onchange_full_name(self):
        """This method is used to compute the contact's full name with a
            combination of the fields first_name, last_name & second_last_name
        """
        if self.first_name:
            self.first_name = self.first_name.title()
        if self.last_name:
            self.last_name = self.last_name.title()
        if self.second_last_name:
            self.second_last_name = self.second_last_name.title()
        self.contact_name = ' '.join([n for n in [
            self.first_name, self.last_name, self.second_last_name] if n])

    @api.model
    def create(self, vals):
        # if the lead is created without neither contact's first name, lastname
        # nor second last name (e.g. when created from an incoming email), fill
        # those fields parsing them from the contact's full name
        if (vals.get('contact_name') and not vals.get('first_name')
                and not vals.get('last_name')
                and not vals.get('second_last_name')):
            first_name, last_name, second_last_name = self.env[
                'res.partner'].split_full_name(vals.get('contact_name'))
            vals.update({
                'first_name': first_name,
                'last_name': last_name,
                'second_last_name': second_last_name,
            })
        # When the leads are imported by IMPORT option
        # Odoo avoids send notifications in the new records
        # obviously to make the import faster.
        # But the user wants the notifications to be sent.
        # Manage the context in base.automation can be complicated.
        ctx = self.env.context.copy()
        if 'import_file' not in ctx:
            return super(Lead, self).create(vals)
        # Allow send message "Dear.. Has been assigned to lead/opportunity"
        # In the log of the new record imported
        # Please, read the documentation in the import.js file of this
        # module if you have doubts about the 'dryrun' attribute of this
        # conditional
        if (self.env.user.company_id.crm_import_notification_enabled and
                'tracking_disable' in ctx and
                ctx.get('dryrun', True) is False):
            del ctx['tracking_disable']
            self = self.with_context(ctx)
        res = super(Lead, self).create(vals)
        # Assign the responsible of the channel to the new lead
        if 'user_id' not in vals and 'team_id' in vals:
            team = self.env['crm.team'].search([('id', '=', vals['team_id'])])
            res.write({'user_id': team.user_id.id})
        # The user in charge of importing files is kept as a follower
        # only if the imported lead belongs to him.
        if vals.get('user_id') != self.env.user.id:
            res.message_unsubscribe([self.env.user.id])
        return res

    #TODO QUITAR @api.multi
    def _track_template(self, tracking):
        """ If the lead stage has changed, and that stage has set an associated
            mail template, send an email using that associated email template
        """
        res = super(Lead, self)._track_template(tracking)
        for lead in self:
            changes = tracking
            # if 'stage_id' in changes:
            if lead.type != 'opportunity':
                if lead.medium_id and lead.medium_id.id == '12':
                    mail = self.env['mail.template'].search([('id', '=', 63)])
                    if mail:
                        res['stage_id'] = (mail, {
                            'auto_delete_message': True,
                        })
                        return res
                if lead.medium_id and lead.medium_id.id == '13':
                    mail = self.env['mail.template'].search([('id', '=', 66)])
                    if mail:
                        res['stage_id'] = (mail, {
                            'auto_delete_message': True,
                        })
                        return res
                if lead.crm_forms_id and lead.crm_forms_id.email_template_form:
                    mail = lead.crm_forms_id.email_template_form
                    if mail:
                        res['stage_id'] = (mail, {
                            'auto_delete_message': True,
                        })
                        return res
                if lead.stage_id.template_id:
                    res['stage_id'] = (lead.stage_id.template_id, {
                        'auto_delete_message': True,
                    })
        return res

    #TODO QUITAR @api.multi
    def message_partner_info_from_emails(self, emails, link_mail=False):
        """ This sets default values for the pop-up dialog which is shown when
            trying to send a message to a partner who is not created yet
        """
        result = super(Lead, self).message_partner_info_from_emails(
            emails, link_mail)
        partner_model = self.env['res.partner']
        for partner_info in result:
            # if the message isn't being sent to a partner but an email
            if not partner_info.get('partner_id'):
                # Creates the company if not already created
                # TODO This search should be improved, A separate method should
                # be created to do this. When the lead is converted to an
                # opportunity and the customer is created, the company is also
                # created and could be duplicated, because it is not taken into
                # account if the company already exists
                partner_company = partner_model
                if self.partner_name:
                    partner_company = partner_model.search([
                        ('name', '=ilike', self.partner_name),
                        ('is_company', '=', True),
                    ], limit=1)
                    if not partner_company:
                        partner_company = partner_model.create(
                            self._create_lead_partner_data(
                                self.partner_name, True))
                ctx = {
                    'default_%s' % field: value
                    for field, value in self._create_lead_partner_data(
                        self.contact_name, False,
                        partner_company.id).items()
                    if value
                }
                ctx['src_model'] = self._name
                partner_info['context'] = ctx
                break
        return result

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ When a lead is created from an incoming email, fill correctly name
            and email, parsing them from the email's sender
        """
        if custom_values is None:
            custom_values = {}
        full_name, email = parseaddr(msg_dict.get('from'))
        if not full_name:
            full_name = email
        defaults = {
            # first, last and 2nd last name will be parsed later on create()
            'contact_name': full_name,
            'email_from': email,
        }
        defaults.update(custom_values)
        return super(Lead, self).message_new(msg_dict, custom_values=defaults)

    @api.constrains('contact_name')
    def _check_contact_name(self):
        if not self.env['res.partner'].is_valid_name(self.contact_name or ''):
            raise ValidationError(_(
                "Contact's name may not contain numbers. Please, try again."))