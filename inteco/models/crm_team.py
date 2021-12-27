# -*- coding: utf-8 -*-

from odoo import fields, models


class Team(models.Model):
    _inherit = 'crm.team'

    subservice_ids = fields.One2many('crm.subservice', 'crm_team_id',
                                     string="Subservices")

    def _alias_get_creation_values(self):
        """ The method :meth:`~.get_alias_values is used to define default
            values for records created from an alias (e.g. created from an
            incoming email).

            In this case, we extend this method to add the following default
            values when a lead is created:
            - Campaign
            - Source
            - Medium

            The above fields are set taking their values from the corresponding
            config parameters. For instance, the campaign is set taking its
            value from the parameter ``default_lead_email_campaign``.

            Note: even though we're setting default values for leads, we
            inherit this method in ``crm.team`` because the creation of leads
            from incoming emails is managed by teams, which are who receive
            emails.
        """
        values = super(Team, self)._alias_get_creation_values()

        # Retrieves default values from parameters
        get_param = self.env['ir.config_parameter'].sudo().get_param
        campaign_id = int(get_param('lead_email_campaign')) or False
        medium_id = int(get_param('lead_email_medium')) or False
        source_id = int(get_param('lead_email_source')) or False
        team_id = int(self.id)
        user_id = int(self.user_id.id)
        values.update({'alias_defaults': {
            'campaign_id': campaign_id,
            'medium_id': medium_id,
            'source_id': source_id,
            'team_id': team_id,
            'user_id': user_id,
        }
        })
        # values['alias_defaults'].update({
        #     'campaign_id': campaign_id,
        #     'medium_id': medium_id,
        #     'source_id': source_id,
        # })
        return values
