# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


DOMAIN = []

class IntecoRegistrationEventChanges(models.Model):
    _inherit = "event.registration"

    att_interest_topics = fields.Many2many(comodel_name="res.partner.category", string='Temas de interés')
    att_id_type = fields.Many2one(comodel_name="identification.type", string='Tipo de Identificación')
    att_ident = fields.Char(string='Identificación')
    att_position = fields.Char(string='Puesto')
    att_name = fields.Char(string='Nombre')
    att_firstname = fields.Char( string='Apellido 1')
    att_lastname = fields.Char(string='Apellido 2')
    contact_id = fields.Many2one(comodel_name="res.partner", string="Contacto", required=False, )
    
    @api.model
    def create(self, vals):
        
        vals = self.prepare_values(vals)
        return super(IntecoRegistrationEventChanges, self).create(vals)
    
    def write(self, values):
        contact_name = values.get('att_name', False) or self.att_name
        att_firstname = values.get('att_firstname', False) or self.att_firstname
        att_lastname = values.get('att_lastname', False) or self.att_lastname
        
        # esta condicion es porque cuando vienen del sitio web los campos vienen vacios
        if not (contact_name == False and att_firstname == False and att_lastname == False):
            name = contact_name + ' ' + att_firstname + ' ' + (att_lastname or '')
            values.update({'name': name})
        
        return super(IntecoRegistrationEventChanges, self).write(values)
    
    def prepare_values(self, vals):
        keys_to_delete = []
        
        tag_ids = []
        for key, value in vals.items():
            if key.startswith('tag_ids'):
                # aqui se hace un replace y funciona porque el valor viene en la misma key
                tag_ids.append([4, int(key.replace('tag_ids', ''))])
                keys_to_delete.append(key)

        
        if vals.get('event_id', False):
            # Para cargar los temas de interes por defecto del evento
            event = self.env['event.event'].sudo().search([('id', '=', vals.get('event_id', False))])
            for interest_topic in event.interest_topics.ids:
                tag_ids.append([4, interest_topic])

        if tag_ids:
            vals['att_interest_topics'] = tag_ids
        
        if vals.get('name', False):
            vals['att_name'] = vals['name']
    
        if vals.get('name', False):
            vals['name'] = vals.get('name', '')+' '+vals.get('firstname', '')+' '+vals.get('lastname', '')
    
        if vals.get('firstname', False):
            vals['att_firstname'] = vals['firstname']
            del vals['firstname']
    
        if vals.get('lastname', False):
            vals['att_lastname'] = vals['lastname']
            del vals['lastname']
        else:
            # vals['att_lastname'] = '' TODO esto borra el segundo apellido si se crea el asistente del sitio web
            if vals.get('lastname', False) == '':
                del vals['lastname']
    
        if vals.get('types_identification', False):
            vals['att_id_type'] = vals['types_identification']
            del vals['types_identification']
    
        if vals.get('position', False):
            vals['att_position'] = vals['position']
            del vals['position']
    
        if vals.get('idatt', False):
            vals['att_ident'] = vals['idatt']
            del vals['idatt']
    
        if vals.get('ticket_id', False):
            vals['event_ticket_id'] = int(vals['ticket_id'])
            del vals['ticket_id']
    
        
        for key, value in vals.items():
            if key.startswith('answer_ids-'):
                keys_to_delete.append(key)
    
        answer_ids = []
        for key, value in vals.items():
            if key.startswith('answer_ids'):
                question_id = int(key[11:])
                if value.isnumeric() is True:
                    answer = {
                        'question_id': question_id,
                        'value_answer_id': int(value),
                    }
                else:
                    answer = {
                        'question_id': question_id,
                        'value_text_box': value,
                    }
                answer_ids.append((0, 0, answer))
    
        if answer_ids:
            vals['registration_answer_ids'] = answer_ids
    
        for key in keys_to_delete:
            del vals[key]
            
        return vals

    def action_confirm(self):
        if self:
            name = (self.att_name or '') + ' ' + (self.att_firstname or '') + ' ' + (self.att_lastname or '')
    
            identification_id = self.att_id_type and self.att_id_type.id or False,
            if identification_id:
                identification_id = int(identification_id[0])
            
            contact_info = {
                "company_type": "person",
                "contact_name": self.att_name,
                "contact_last_name": self.att_firstname,
                "second_last_name": self.att_lastname,
                "name": name,
                "identification_id": identification_id,
                "ref": self.att_ident,
                "email": self.email,
                "phone": self.phone,
                "mobile": self.mobile,
            }
            contact_id = self.create_update_contact(contact_info)
            values = {
                "contact_id": contact_id,
                'state': 'open'
            }
            self.write(values)
        
    def create_update_contact(self, vals):
        partner_obj = self.env['res.partner']
        partner = partner_obj.search([('email', '=', vals.get('email'))])
        if len(partner) >= 1:
            if partner.company_type != 'company':
                partner.write(vals)
                return partner
            else:
                return partner
        else:
            return partner_obj.create(vals)
            