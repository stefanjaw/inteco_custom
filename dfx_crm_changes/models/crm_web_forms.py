from odoo import models, fields, api, _


class CrmWebForms(models.Model):
    _name = "crm.forms"
    _description = 'Formularios para creacion de leads en sitio web'

    name_form = fields.Char(string="Nombre")
    team_form = fields.Many2one(comodel_name='crm.team', string="Equipo")
    opportunity = fields.Char(string="Asunto de oportunidad", )
    subservice_form = fields.Many2one(comodel_name='crm.subservice', string="Subservicio")
    email_template_form = fields.Many2one(comodel_name='mail.template', string="Plantilla de Correo")
    media_form = fields.Many2one(comodel_name='utm.medium', string="Media")

    _rec_name = 'name_form'