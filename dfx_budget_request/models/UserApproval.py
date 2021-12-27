import re
from odoo import models, fields, api, _


class UserAprovdbr(models.Model):  # dbr = dfx_budget_request
    _name = "user.approval"
    _description = 'Personas que aprueban'

    user_place = fields.Many2one(comodel_name='user.depart', string="Dirección", store="True")
    user_requester = fields.Many2one(comodel_name='res.users', string="Solicitador", default=lambda self: self.env['res.users'].search([], limit=1))
    user_approb1 = fields.Many2one(comodel_name='res.users', string="Aprobador 1")
    user_approb1_bk = fields.Many2one(comodel_name='res.users' ,string="Aprobador 1 (Back up)")
    user_approb2 = fields.Many2one(comodel_name='res.users', string="Aprobador 2")

    _rec_name = 'user_place'

    # metodo para validar si el solicitante es igual al aprobador 1
    @api.onchange('user_approb1')
    def valida_approv1(self):
        for record in self:
            if record.user_requester == record.user_approb1:
                record.user_approb1 = ''
                return {

                    'warning': {

                        'title': 'Aprobación Restringida!',

                        'message': 'Motivo: Usted no puede ser su propio aprobador, Favor contactar al encargado del sistema!'}

                }

    # metodo para validar si el solicitante es igual al aprobador 2
    @api.onchange('user_approb2')
    def valida_approv2(self):
        for record in self:
            if record.user_requester == record.user_approb2:
                record.user_approb2 = ''
                return {

                    'warning': {

                        'title': 'Aprobación Restringida!',

                        'message': 'Motivo: Usted no puede ser su propio aprobador, Favor contactar al encargado del sistema!'}

                }

    # metodo para validar si el solicitante es igual al backup del aprobador 1
    @api.onchange('user_approb1_bk')
    def valida_approvbk(self):
        for record in self:
            if record.user_requester == record.user_approb1_bk:
                record.user_approb1_bk = ''
                return {

                    'warning': {

                        'title': 'Aprobación Restringida!',

                        'message': 'Motivo: Usted no puede ser su propio aprobador, Favor contactar al encargado del sistema!'}

                }