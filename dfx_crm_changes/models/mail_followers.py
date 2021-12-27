# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class FollowersInherit(models.Model):
    _inherit = 'mail.followers'

    @api.model_create_multi
    def create(self, vals_list):
        if vals_list[0].get('res_model', False) and vals_list[0].get('res_model', False) == 'crm.lead':
            partner_id = vals_list[0].get('partner_id', False)
            res_id = vals_list[0].get('res_id', False)
            rec = self.search([('res_id', '=', res_id), ('partner_id', '=', partner_id)])
            if len(rec) >= 1:
                rec.unlink()
            
        res = super(FollowersInherit, self).create(vals_list)
        res._invalidate_documents(vals_list)
        return res