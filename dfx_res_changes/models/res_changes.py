# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime, timedelta
from pytz import timezone

class ActivityTypeInherit(models.Model):
    _inherit = "res.company"
    _description = 'añadir tipo de actividad por defecto'

    mail_activity_purchase = fields.Many2one(comodel_name='mail.activity.type', string="Tipo de Actividad por defecto",
                                             help=('este campo se utiliza para crear una actividad automática a la hora '
                                                   'de realizar una solicitud de presupuesto en el modulo de compras'))

class Remove_condition(models.Model):
    _inherit = "res.partner"
    _description = 'remueve la condición de no repetir correos en el modulo de contactos'

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    contact_id = fields.Char(string="Cédula", required=False, )

    ref = fields.Char(string='Cédula', index=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    # emails_ids = fields.One2many(comodel_name="mails.electronic.invoice", inverse_name="res_partner_id",
    #                              string='Correos electrónicos adicionales para FE',
    #                              help="Solo ingresar correos electrónicos adicionales, es necesario el correo electrónico principal en el campo “Correo”, solo se utilizaran para enviar los documentos electrónicos de facturación electrónica.")
    comment = fields.Text(string='Notas', tracking=True)
    phone = fields.Char(string='Teléfono', tracking=True)
    mobile = fields.Char(string='Móvil', tracking=True)
    country_id = fields.Many2one('res.country', string='País', ondelete='restrict', tracking=True)
    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                   column2='category_id', string='Etiquetas', default=_default_category)

    #@api.multi
    def write(self, vals):
        res = super(Remove_condition, self).write(vals)
        import calendar
        date_today = datetime.now()
        date_day = date_today.strftime("%d")
        date_month = date_today.strftime("%m")
        date_month_name = calendar.month_name[int(date_month)]
        date_year = date_today.strftime("%Y")
        fmt = "%I:%M %p"
        now_utc = datetime.now(timezone('UTC'))
        now_pac = now_utc.astimezone(timezone(self.env.user.tz))
        date_time = now_pac.strftime(fmt)
        user = self.env.user.name
        if vals.get('emails_ids',False):
            self.message_post(
                body="El usuario:" + " " + user + ", " + "realizó cambios en el campo: Correos electrónicos adicionales para FE, el día" + " " + str(
                    date_day + " " + date_month_name + " " + "del" + " " + date_year) + " " + "a las" + " " + str(
                    date_time))

        if vals.get('category_id', False):
            self.message_post(
                body="El usuario:" + " " + user + ", " + "realizó cambios en el campo: Etiquetas, el día" + " " + str(
                    date_day + " " + date_month_name + " " + "del" + " " + date_year) + " " + "a las" + " " + str(
                    date_time))

        return res

    #@api.multi
    def _check_email_duplicated(self):
        pass
        # """Ensures that the email address is unique for each contact. We
        # decided to use an onchange instead of a constraint due to there are
        # a lot of previously registered emails."""
        # # I prefer to use "- self" to avoid the current line
        # # because if I add the tuple ('id', '!=', self.id),
        # # when the partner is a new partner can occurs
        # # the following error:
        # # ProgrammingError: can't adapt type 'NewId'
        # # because line.id will be
        # # <odoo.models.NewId object at 0x7f6a47fd9750>
        # partner = self.sudo().search([
        #     ('email', '=', self.email)]) - self \
        #     if self.email else False
        # if partner:
        #     raise ValidationError(
        #         _(
        #             'Take into account that the following contact already'
        #             'has the same email registered: \n\n- %s <%s>') % (
        #             partner.display_name, partner.email))

    # vat = fields.Char(copmute='validate_nif')

    # #@api.multi
    # def _check_nif_duplicated(self):
    #     for rec in self:
    #         partner = rec.sudo().search([
    #             ('vat', '=', rec.vat)]) - rec \
    #             if rec.vat else False
    #         if partner:
    #             raise ValidationError(
    #                 _(
    #                     'El siguiente usuario posee el mismo numero de identificación(NIF). Favor revisar: \n\n- %s <%s>') % (
    #                     partner.display_name, partner.vat))
    #
    # @api.constrains('vat')
    # def _check_nif(self):
    #     for record in self:
    #         if record.vat:
    #             record._check_nif_duplicated()

class Check_Password(models.Model):
    _inherit = "res.users"

    def _set_password(self):
        ctx = self._crypt_context()
        for user in self:
            self._set_encrypted_password(user.id, ctx.encrypt(user.password))

    def _set_encrypted_password(self, uid, pw):
        assert self._crypt_context().identify(pw) != 'plaintext'

        self.env.cr.execute(
            'UPDATE res_users SET password=%s WHERE id=%s',
            (pw, uid)
        )
        self.invalidate_cache(['password'], [uid])