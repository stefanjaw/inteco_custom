
from odoo import fields, models


DEFAULT_LEAD_PARAMS = (
    'lead_email_campaign',
    'lead_email_medium',
    'lead_email_source',
    'lead_website_campaign',
    'lead_website_medium',
    'lead_website_source',
)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lead_email_campaign_id = fields.Many2one(
        default_model='utm.campaign', string="Default campaign for emails", comodel_name="utm.campaign")
    lead_email_medium_id = fields.Many2one(
        default_model='utm.medium', string="Default medium for emails", comodel_name="utm.medium")
    lead_email_source_id = fields.Many2one(
        default_model='utm.source', string="Default source for emails", comodel_name="utm.source")
    lead_website_campaign_id = fields.Many2one(
        default_model='utm.campaign', string="Default campaign for the website", comodel_name="utm.campaign")
    lead_website_medium_id = fields.Many2one(
        default_model='utm.medium', string="Default medium for the website", comodel_name="utm.medium")
    lead_website_source_id = fields.Many2one(
        default_model='utm.source', string="Default source for the website", comodel_name="utm.source")
    crm_import_notification_enabled = fields.Boolean(
        string="Send Notification on Import",
        related='company_id.crm_import_notification_enabled')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update({
            param + '_id': int(get_param(param))
            for param in DEFAULT_LEAD_PARAMS
        })
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        for param in DEFAULT_LEAD_PARAMS:
            set_param(param, getattr(self, param + '_id').id)
        teams = self.env['crm.team'].search([
            ('use_leads', '=', True),
            ('alias_id', '!=', False),
        ])
        for team in teams:
            team.alias_id.write(team._alias_get_creation_values())
        return res
