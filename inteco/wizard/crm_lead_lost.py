# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    lost_company_name = fields.Char(
        string="Competitor's company name",
        help="Company against which the opportunity was lost"
    )

    #TODO QUITAR @api.multi
    def action_lost_reason_apply(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            leads = self.env['crm.lead'].browse(active_ids)
            leads.write({'lost_company_name': self.lost_company_name})
        return super(CrmLeadLost, self).action_lost_reason_apply()
