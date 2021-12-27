# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.fields import Date
from datetime import date, timedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class CRMLead(models.Model):
    _inherit = "crm.lead"

    crm_forms_id = fields.Many2one(comodel_name="crm.forms", string="Formulario", required=False, )
    contact_tags = fields.Many2many(comodel_name="res.partner.category", string="Etiquetas del contacto")
    contact_bool = fields.Boolean(string='check grupo categorias')

    @api.onchange("partner_id")
    def get_cont_tags(self):
        for record in self:
            if record.partner_id:
                if record.partner_id.category_id:
                    for new_etq in record.partner_id.category_id.ids:
                        record.contact_tags = [(4, new_etq)]
                else:
                    record.contact_tags = [(4, 48)]


    def validate_start_key_word(self):
        keywords = self.env['crm.key.words'].search([])
        for key in keywords:
            if self and key.key_word_name.lower() in self.name.lower():
                self.env["crm.lead"].search([('id', '=', self.id)]).unlink()

    @api.model
    def create(self, vals):
        if vals.get('crm_forms_id', False) and vals['crm_forms_id'].isnumeric():
            vals['crm_forms_id'] = int(vals['crm_forms_id'])
    
        if 'user_id' not in vals and 'team_id' in vals:
            team = self.env['crm.team'].search([('id', '=', vals['team_id'])])
            vals.update({'user_id': team.user_id.id})
        return super(CRMLead, self).create(vals)

    def new_automatic_activity(self, activities):
        """Schedules the default activities for the stage."""

        self.ensure_one()
        for activity in activities:
            if not self.env['mail.activity'].search([('res_id','=',self.id),('summary','=',activity.name)]):
                record = {
                    'activity_type_id': activity.id,
                    'summary': activity.name,
                    'date_deadline': self.date_after_wo_weekends(Date.today(), activity.delay_count),
                    'user_id': self.user_id.id,
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': self.id,
                }
                self.env['mail.activity'].create(record)
        self.assigned_activity = True
        return True

    @api.model
    def date_after_wo_weekends(self, start_date, delay_count):
        """Given a date and a number of working days, returns the effective
            date in which a task would be completed, excluding weekends
        """
        if isinstance(start_date, str):
            start_date = Date.from_string(start_date)
        start_weekday = start_date.weekday()
        worked_days = 0
        position = 0
        weekend_days = 0
        while worked_days < delay_count:
            position += 1
            position_weekday = (start_weekday + position) % 7
            if position_weekday > 4:  # weekend
                weekend_days += 1
            else:
                worked_days += 1
        return start_date + timedelta(days=delay_count + weekend_days)

    def website_form_input_filter(self, request, values):
        """Change values if request has crm_forms_id
        """
        super(CRMLead, self).website_form_input_filter(request, values)
        form = request.params.get('crm_forms_id') or False
        if form:
            new_values = {}
            crm_form_id = self.env['crm.forms'].browse(int(form))

            subject = crm_form_id.opportunity or ''
            subservice_id = crm_form_id.subservice_form.id or False
            medium_id = crm_form_id.media_form.id or False
            team_id = crm_form_id.team_form.id or False

            new_values.update({
                'name': subject,
                'medium_id': medium_id,
                'subservice_id': subservice_id,
                'crm_forms_id': form,
                'team_id': int(team_id),
            })

            subservice = request.env['crm.subservice'].search([
                ('id', '=', subservice_id)
            ])
            if subservice.responsible_id:
                new_values.update({'user_id': subservice.responsible_id.id})
            values.update(new_values)
        return values

    #@api.multi
    def _track_template(self, tracking):
        """ If the lead stage has changed, and crm_forms_id is defined
            send an email using that associated email template in crm_forms_id.email_template_form
        """
        res = super(CRMLead, self)._track_template(tracking)
        for lead in self:
            changes = tracking
            # if 'stage_id' in changes:
            # if lead.crm_forms_id and lead.crm_forms_id.email_template_form:
            n = self.env['crm.forms'].search([('id', '=', lead.crm_forms_id.id)])
            if lead.crm_forms_id:
                mail = n.email_template_form
                if mail:
                    res['stage_id'] = (mail, {
                        'auto_delete_message': False,
                    })
                    return res
            if lead.stage_id.template_id:
                res['stage_id'] = (lead.stage_id.template_id, {
                    'auto_delete_message': True,
                })
        return res

    def _pls_get_naive_bayes_probabilities(self, batch_mode=False):
        """
        In machine learning, naive Bayes classifiers (NBC) are a family of simple "probabilistic classifiers" based on
        applying Bayes theorem with strong (naive) independence assumptions between the variables taken into account.
        E.g: will TDE eat m&m's depending on his sleep status, the amount of work he has and the fullness of his stomach?
        As we use experience to compute the statistics, every day, we will register the variables state + the result.
        As the days pass, we will be able to determine, with more and more precision, if TDE will eat m&m's
        for a specific combination :
            - did sleep very well, a lot of work and stomach full > Will never happen !
            - didn't sleep at all, no work at all and empty stomach > for sure !
        Following Bayes' Theorem: the probability that an event occurs (to win) under certain conditions is proportional
        to the probability to win under each condition separately and the probability to win. We compute a 'Win score'
        -> P(Won | A∩B) ∝ P(A∩B | Won)*P(Won) OR S(Won | A∩B) = P(A∩B | Won)*P(Won)
        To compute a percentage of probability to win, we also compute the 'Lost score' that is proportional to the
        probability to lose under each condition separately and the probability to lose.
        -> Probability =  S(Won | A∩B) / ( S(Won | A∩B) + S(Lost | A∩B) )
        See https://www.youtube.com/watch?v=CPqOCI0ahss can help to get a quick and simple example.
        One issue about NBC is when a event occurence is never observed.
        E.g: if when TDE has an empty stomach, he always eat m&m's, than the "not eating m&m's when empty stomach' event
        will never be observed.
        This is called 'zero frequency' and that leads to division (or at least multiplication) by zero.
        To avoid this, we add 0.1 in each frequency. With few data, the computation is than not really realistic.
        The more we have records to analyse, the more the estimation will be precise.
        :return: probability in percent (and integer rounded) that the lead will be won at the current stage.
        """
        lead_probabilities = {}
        if not self:
            return lead_probabilities

        # Get all leads values, no matter the team_id
        domain = []
        if batch_mode:
            domain = [
                '&',
                ('active', '=', True), ('id', 'in', self.ids),
                '|',
                ('probability', '=', None),
                '&',
                ('probability', '<', 100), ('probability', '>', 0)
            ]
        leads_values_dict = self._pls_get_lead_pls_values(domain=domain)

        if not leads_values_dict:
            return lead_probabilities

        # Get unique couples to search in frequency table and won leads.
        leads_fields = set()  # keep unique fields, as a lead can have multiple tag_ids
        won_leads = set()
        won_stage_ids = self.env['crm.stage'].search([('is_won', '=', True)]).ids
        for lead_id, values in leads_values_dict.items():
            for field, value in values['values']:
                if field == 'stage_id' and value in won_stage_ids:
                    won_leads.add(lead_id)
                leads_fields.add(field)

        # get all variable related records from frequency table, no matter the team_id
        frequencies = self.env['crm.lead.scoring.frequency'].search([('variable', 'in', list(leads_fields))], order="team_id asc")

        # get all team_ids from frequencies
        frequency_teams = frequencies.mapped('team_id')
        frequency_team_ids = [0] + [team.id for team in frequency_teams]

        # 1. Compute each variable value count individually
        # regroup each variable to be able to compute their own probabilities
        # As all the variable does not enter into account (as we reject unset values in the process)
        # each value probability must be computed only with their own variable related total count
        # special case: for lead for which team_id is not in frequency table,
        # we consider all the records, independently from team_id (this is why we add a result[-1])
        result = dict((team_id, dict((field, dict(won_total=0, lost_total=0)) for field in leads_fields)) for team_id in frequency_team_ids)
        result[-1] = dict((field, dict(won_total=0, lost_total=0)) for field in leads_fields)
        for frequency in frequencies:
            team_result = result[frequency.team_id.id if frequency.team_id else 0]

            field = frequency['variable']
            value = frequency['value']

            # To avoid that a tag take to much importance if his subset is too small,
            # we ignore the tag frequencies if we have less than 50 won or lost for this tag.
            if field == 'tag_id' and (frequency['won_count'] + frequency['lost_count']) < 50:
                continue

            team_result[field][value] = {'won': frequency['won_count'], 'lost': frequency['lost_count']}
            team_result[field]['won_total'] += frequency['won_count']
            team_result[field]['lost_total'] += frequency['lost_count']

            if value not in result[-1][field]:
                result[-1][field][value] = {'won': 0, 'lost': 0}
            result[-1][field][value]['won'] += frequency['won_count']
            result[-1][field][value]['lost'] += frequency['lost_count']
            result[-1][field]['won_total'] += frequency['won_count']
            result[-1][field]['lost_total'] += frequency['lost_count']

        # Get all won, lost and total count for all records in frequencies per team_id
        for team_id in result:
            result[team_id]['team_won'], \
            result[team_id]['team_lost'], \
            result[team_id]['team_total'] = self._pls_get_won_lost_total_count(result[team_id])

        save_team_id = None
        p_won, p_lost = 1, 1
        for lead_id, lead_values in leads_values_dict.items():
            # if stage_id is null, return 0 and bypass computation
            lead_fields = [value[0] for value in lead_values.get('values', [])]
            if not 'stage_id' in lead_fields:
                lead_probabilities[lead_id] = 0
                continue
            # if lead stage is won, return 100
            elif lead_id in won_leads:
                lead_probabilities[lead_id] = 100
                continue

            lead_team_id = lead_values['team_id'] if lead_values['team_id'] else 0  # team_id = None -> Convert to 0
            lead_team_id = lead_team_id if lead_team_id in result else -1  # team_id not in frequency Table -> convert to -1
            if lead_team_id != save_team_id:
                save_team_id = lead_team_id
                team_won = result[save_team_id]['team_won']
                team_lost = result[save_team_id]['team_lost']
                team_total = result[save_team_id]['team_total']
                # if one count = 0, we cannot compute lead probability
                if not team_won or not team_lost:
                    continue
                p_won = team_won / team_total
                p_lost = team_lost / team_total

            # 2. Compute won and lost score using each variable's individual probability
            s_lead_won, s_lead_lost = p_won, p_lost
            for field, value in lead_values['values']:
                field_result = result.get(save_team_id, {}).get(field)
                value = value.origin if hasattr(value, 'origin') else value
                value_result = field_result.get(str(value)) if field_result else False
                if value_result:
                    total_won = team_won if field == 'stage_id' else field_result['won_total']
                    total_lost = team_lost if field == 'stage_id' else field_result['lost_total']

                    if total_won == 0.0:
                        s_lead_won = 0.0
                    else:
                        s_lead_won *= value_result['won'] / total_won

                    if total_lost == 0:
                        s_lead_lost = 0
                    else:
                        s_lead_lost *= value_result['lost'] / total_lost


            # 3. Compute Probability to win
            if round(s_lead_won) or round(s_lead_lost) == 0:
                lead_probabilities[lead_id] = 0
            else:
                lead_probabilities[lead_id] = round(100 * s_lead_won / (s_lead_won + s_lead_lost), 2)
        return lead_probabilities


class IntecoCrmTags(models.Model):
    _inherit = "res.partner.category"

    @api.model
    def create(self, values):
        """
        Rellena el campo factura proforma
        """
        rec = super(IntecoCrmTags, self).create(values)
        if rec.user_has_groups('dfx_crm_changes.crm_contact_tag_manager'):
            pass
        else:
            raise ValidationError(
                _('Alerta, no posee permisos para crear etiquetas'))
        return rec

