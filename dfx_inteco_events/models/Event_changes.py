# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


DOMAIN = []


class IntecoQuestionEventChanges(models.Model):
    _inherit = "event.question.answer"

    valid_event_anw = fields.Boolean(string='Es inválida')


class IntecoEventChanges(models.Model):
    _inherit = "event.event"
    _description = 'cambios en el modulo de eventos para Inteco'

    interest_topics = fields.Many2many(comodel_name="res.partner.category", string='Temas de interés')
    event_platform = fields.Many2one(comodel_name="event.platform", string='Plataforma')
    event_location = fields.Char(string='Lugar')
    event_google_maps = fields.Char(string='Enlace Google Maps')
    social_hashtags = fields.Char(string='Hashtag para redes')
    has_event_group = fields.Boolean(string='Tiene permiso de evento?', compute='serv_calc_group')
    is_event_online = fields.Boolean(string='En línea')
    firstname = fields.Char(string='Apellido 1')
    lastname = fields.Char(string='Apellido 2')
    idtype = fields.Boolean(string='Tipo de Identificacion')
    idatt = fields.Char(string='Identificacion')
    position = fields.Char(string='Posicion')
    event_organizers = fields.Many2many('event.organizer','event_organizer_rel','org_name', string="Co Organiza")
    event_co_organizers = fields.Many2many('event.organizer','event_co_organizer_rel','org_name', string="Patrocina")
    event_invite = fields.Many2many('event.organizer','event_invite_rel','org_name', string="Invita")
    #Cambia el campo original por uno custom
    organizer_id2 = fields.Many2one(comodel_name='event.organizer', string="Organiza")

    @api.onchange('event_co_organizers')
    def valid_org(self):
        for record in self:
            for ext_org in record.event_co_organizers.ids:
                if ext_org in record.event_organizers.ids:
                    raise ValidationError(
                        _('Alerta, un co-organizador no puede ser organizador a la vez. Favor revisar!'))


    def serv_calc_group(self):
        for record in self:
            if record.user_has_groups('event.group_event_manager'):
                record.has_event_group = True
            else:
                record.has_event_group = False

    # @api.one
    def button_confirm(self):
        partner_etq = self.env['res.partner'].search([('id', '=', self.organizer_id.id)])
        for new_etq in self.interest_topics.ids:
            if new_etq not in partner_etq.category_id.ids:
                partner_etq.category_id = [(4, new_etq)]
        self.state = 'confirm'
