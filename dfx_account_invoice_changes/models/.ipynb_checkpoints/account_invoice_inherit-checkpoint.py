# -*- coding: utf-8 -*-
from odoo import models, fields, api, http, _
from datetime import datetime
# from pytz import timezone
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import requests
# from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
#     pycompat, date_utils

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('open', 'Abierto'),
            ('in_payment', 'En proceso de pago'),
            ('no_valid', 'Anulado'),
            ('posted', 'Publicado'),  # paid Pagado
            ('cancel', 'Cancelada')
        ],
    )
    after_date_days = fields.Char(string="Días Moroso", store="True")
    day = fields.Char(string="Días", store="True")
    mon = fields.Char(string="Mes", store="True")
    year = fields.Char(string="Año", store="True")
    day_num = fields.Char(string="dia num", store="True")
    lb_green = fields.Boolean(string="Cliente Inteco", store="True")
    lb_yellow = fields.Boolean(string="Cliente a Revisar", store="True")
    lb_red = fields.Boolean(string="Sin Crédito", store="True")
    exchange_rate_test = fields.Float(compute="exchange_calc", string="Tipo de Cambio", readonly=True, store=True)

    def action_post(self):
        if self.move_type == 'out_invoice':
            for rec in self.invoice_line_ids:
                if rec:
                    if rec.analytic_account_id:
                        pass
                    else:
                        raise UserError(
                            _('Se encontraron cuentas analíticas vacías, favor revisar!.'))
        super(AccountMoveInherit, self).action_post()


    def check_analitic_accounts(self):
        if self.move_type == 'out_invoice':
            for rec in self.invoice_line_ids:
                if rec:
                    if rec.analytic_account_id:
                        pass
                    else:
                        raise UserError(
                            _('Se encontraron cuentas analíticas vacías, favor revisar!.'))

    # Método para calcular el tipo de cambio según el bccr
    @api.onchange('currency_id')
    def exchange_calc(self):
        for record in self:
            if record.currency_id.rate:
                record.exchange_rate_test = record.currency_id.rate
                # round(record.currency_id.rate)

    # Se hereda el metodo original de FE
    def _consult(self, inv, number, config):
        super(AccountMoveInherit, self)._consult(inv, number, config)
        if inv.state_tributacion == 'rechazado':
            email_template = self.env.ref('dfx_account_invoice_changes.template_electronic_invoice_rejected', False)
            email_template.send_mail(inv.id, raise_exception=False, force_send=True)

    def get_mail_url(self):
        return self._get_share_url(redirect=True, signup_partner=True)

    def action_cancel(self):
        for inv in self:
            if inv.move_id:
                #journal_id = self.env.ref('dfx_account_invoice_changes.reversals_journal', False)
                journal_id = inv.company_id.reversal_journal_id
                inv.move_id.sudo().reverse_moves(fields.Date.today(), journal_id)
                mail_message = self.env['mail.message']
                mail_message.create({
                    'body': '<p>Asiento contable revertido automáticamente.</p>',
                    'model': 'account.move',
                    'res_id': inv.id,
                    'message_type': 'comment',
                })
        self.write({'state': 'cancel'})
        return True

    # todo Alejandro verificar
    # metodo para validar cliente con facturas pendientes
    # @api.onchange('partner_id')
    # def check_inv(self):
    #     today = datetime.now()
    #     # TODO revisar los estados para esta nueva version
    #     partner_inv = self.env['account.move'].search([
    #         ('partner_id', '=', self.partner_id.id),
    #         ('invoice_date_due', '<', today),
    #         ('state', 'not in', ('posted', 'cancel', 'draft', 'no_valid')),
    #         ('payment_state', 'in', ('partial', 'in_payment', 'not_paid')),
    #         ('move_type', '=', 'out_invoice')])
    #
    #     if self.move_type not in ('in_invoice', 'in_refund', 'out_refund'):
    #         if partner_inv:
    #             raise ValidationError(
    #                 _('Alerta, el cliente seleccionado registra facturas pendientes, debe consultar con '
    #                   'cobros@inteco.org, la posibilidad de emitir una nueva factura.'))

    # def _get_emails(self, partner_id):
    #     emails = partner_id.email or ''
    #     for email in partner_id.emails_ids:
    #         if email.name:
    #             emails += ((emails and ', ') or '') + email.name
    #     return emails

    def get_invoices(self):
        if self.partner_id:
            rec = self.env['account.move'].search([
                ('state', 'in', ('open', 'posted')),
                ('payment_state', 'in', ('partial', 'in_payment', 'not_paid')),
                ('partner_id', '=', self.partner_id.id)
            ])
            return rec
        else:
            return None

    def get_latest_invoices(self):
        if self.partner_id:
            rec = self.env['account.move'].search([
                ('state', 'in', ('open', 'posted')),
                ('payment_state', 'in', ('partial', 'in_payment', 'not_paid'))
            ])
            return rec
        else:
            return None

    @api.model
    def check_invoice_fe(self):
        res = self.env['account.move'].search([])
        partner_ids = []
        invoice_ids = []
        #  TODO Las facturas con pagos ahora no aparecen en el campo state, estan en el campo payment_state
        #   Revisar si los estados son los correctos para la version 14
        for rec in self.env['account.move'].search([
            ('state', 'in', ('open', 'posted')),
            ('payment_state', 'in', ('partial', 'in_payment', 'not_paid'))]):
            if rec.partner_id not in partner_ids:
                partner_ids.append(rec.partner_id)
                invoice_ids.append(rec)

        cal = self.env['time.calc.funtions']
        for record in invoice_ids:
            today = datetime.now()
            record.day = today.strftime("%A")
            record.day_num = today.day
            record.mon = today.strftime("%B")
            record.year = today.strftime("%Y")

            val1 = today - today

            # TODO antiguo record.state == 'open' ya no se presenta
            #  Las facturas con pagos estan payment_state
            #  Revisar si los estados son los correctos
            if record.payment_state in ('partial', 'in_payment', 'not_paid', ) and record.invoice_date_due != today:
                val1 = today - datetime.strptime(record.invoice_date_due.strftime('%Y%m%d'), '%Y%m%d')
                record.after_date_days = val1.days

            if val1.days >= 0:
                pass
            else:
                record.after_date_days = 0

            if record.invoice_date_due and record.partner_id.email and record.invoice_date_due != today:
                second_day = cal.cal_bussines_date(datetime.strptime(record.invoice_date.strftime('%Y%m%d'), '%Y%m%d'),48)
                first_day = cal.cal_bussines_date(datetime.strptime(record.invoice_date_due.strftime('%Y%m%d'), '%Y%m%d'), 24)
                twenty_day = cal.cal_bussines_date(datetime.strptime(record.invoice_date.strftime('%Y%m%d'), '%Y%m%d'), 480)
                eight_day = cal.cal_bussines_date(datetime.strptime(record.invoice_date.strftime('%Y%m%d'), '%Y%m%d'),192)
                first_week = cal.cal_bussines_date(first_day, 168)
                second_week = cal.cal_bussines_date(first_week, 168)
                third_week = cal.cal_bussines_date(second_week, 168)
                fourth_week = cal.cal_bussines_date(third_week, 168)
                fifth_week = cal.cal_bussines_date(fourth_week, 168)
                six_week = cal.cal_bussines_date(fifth_week, 168)
                seventh_week = cal.cal_bussines_date(six_week, 168)
                eight_week = cal.cal_bussines_date(seventh_week, 168)
                nine_week = cal.cal_bussines_date(eight_week, 168)
                ten_week = cal.cal_bussines_date(nine_week, 168)
                eleven_week = cal.cal_bussines_date(ten_week, 168)
                twelve_week = cal.cal_bussines_date(eleven_week, 168)

                # if int(record.after_date_days) >= 120:
                #     email_template = self.env.ref('dfx_account_invoice_changes.Reminder120_invoice_email_template')
                #     # email_template.email_to = self._get_emails(record.partner_id)
                #     email_template.send_mail(record.id, raise_exception=False,force_send=True)

                # recordatorio 2 dia
                # TODO if record.state == 'open' and today.date() == second_day.date() and
                #  (record.invoice_payment_term_id.id == 6 or record.invoice_payment_term_id.id == 3):
                #  para invoice_payment_term_id id 3=21 dias id=6 2 meses
                #  Revisar los estados payment_state

                if record.payment_state in ('partial', 'in_payment', 'not_paid', ) and \
                        today.date() == second_day.date() and \
                        (record.invoice_payment_term_id.id == 6 or record.invoice_payment_term_id.id == 3):
                    if record.partner_id.emails_ids:
                        email_template = self.env.ref('dfx_account_invoice_changes.Confirm_invoice_email_template')
                        email_template.email_to = self._get_emails(record.partner_id)
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                    else:
                        email_template = self.env.ref('dfx_account_invoice_changes.Confirm_invoice_email_template')
                        email_template.email_to = record.partner_id.email
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                else:
                    # recordatorio 20 dias
                    if record.payment_state == 'open' and record.invoice_payment_term_id.id == 3 and today.date() == twenty_day.date():
                        if record.partner_id.emails_ids:
                            email_template = self.env.ref('dfx_account_invoice_changes.Reminder20_invoice_email_template')
                            email_template.email_to = self._get_emails(record.partner_id)
                            email_template.send_mail(record.id, raise_exception=False, force_send=True)
                        else:
                            email_template = self.env.ref('dfx_account_invoice_changes.Reminder20_invoice_email_template')
                            email_template.email_to = record.partner_id.email
                            email_template.send_mail(record.id, raise_exception=False, force_send=True)
                    else:
                        # recordatorio 8 dias
                        if record.payment_state == 'open' and today.date() == eight_day.date() and (record.invoice_payment_term_id.id == 1 or record.invoice_payment_term_id.id == 2):
                            if record.partner_id.emails_ids:
                                email_template = self.env.ref('dfx_account_invoice_changes.Reminder08_invoice_email_template')
                                email_template.email_to = self._get_emails(record.partner_id)
                                email_template.send_mail(record.id, raise_exception=False, force_send=True)
                            else:
                                email_template = self.env.ref('dfx_account_invoice_changes.Reminder08_invoice_email_template')
                                email_template.email_to = record.partner_id.email
                                email_template.send_mail(record.id, raise_exception=False, force_send=True)
                        else:
                            # primer recordatorio moroso
                            if record.payment_state == 'open' and int(record.after_date_days) >= 1 and int(record.after_date_days) <= 15 and (today.date() == first_day.date() or today.date() == first_week.date() or today.date() == second_week.date()):
                                if record.partner_id.emails_ids:
                                    email_template = self.env.ref('dfx_account_invoice_changes.First_Reminder_invoice_email_template')
                                    email_template.email_to = self._get_emails(record.partner_id)
                                    email_template.send_mail(record.id, raise_exception=False, force_send=True)
                                else:
                                    email_template = self.env.ref('dfx_account_invoice_changes.First_Reminder_invoice_email_template')
                                    email_template.email_to = record.partner_id.email
                                    email_template.send_mail(record.id, raise_exception=False, force_send=True)
                            else:
                                # segundo recordatorio moroso
                                if record.payment_state == 'open' and int(record.after_date_days) >= 16 and int(record.after_date_days) <= 30 and (today.date() == third_week.date() or today.date() == fourth_week.date()):
                                    if record.partner_id.emails_ids:
                                        email_template = self.env.ref('dfx_account_invoice_changes.Second_Reminder_invoice_email_template')
                                        email_template.email_to = self._get_emails(record.partner_id)
                                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                                    else:
                                        email_template = self.env.ref('dfx_account_invoice_changes.Second_Reminder_invoice_email_template')
                                        email_template.email_to = record.partner_id.email
                                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                                else:
                                    # tercer recordatorio moroso
                                    if record.payment_state == 'open' and int(record.after_date_days) > 30 and int(record.after_date_days) <= 90 and (today.date() == fifth_week.date() or today.date() == six_week.date() or today.date() == seventh_week.date() or today.date() == eight_week.date()):
                                        if record.partner_id.emails_ids:
                                            email_template = self.env.ref('dfx_account_invoice_changes.Third_Reminder_invoice_email_template')
                                            email_template.email_to = self._get_emails(record.partner_id)
                                            email_template.send_mail(record.id, raise_exception=False, force_send=True)
                                        else:
                                            email_template = self.env.ref('dfx_account_invoice_changes.Third_Reminder_invoice_email_template')
                                            email_template.email_to = record.partner_id.email
                                            email_template.send_mail(record.id, raise_exception=False, force_send=True)
                                    else:
                                        # cuarto recordatorio moroso
                                        if record.payment_state == 'open' and int(record.after_date_days) > 30 and int(record.after_date_days) <= 90 and (today.date() == nine_week.date() or today.date() == ten_week.date() or today.date() == eleven_week.date() or today.date() == twelve_week.date()):
                                            if record.partner_id.emails_ids:
                                                email_template = self.env.ref('dfx_account_invoice_changes.Fourth_Reminder_invoice_email_template')
                                                email_template.email_to = self._get_emails(record.partner_id)
                                                email_template.send_mail(record.id, raise_exception=False,force_send=True)
                                            else:
                                                email_template = self.env.ref('dfx_account_invoice_changes.Fourth_Reminder_invoice_email_template')
                                                email_template.email_to = record.partner_id.email
                                                email_template.send_mail(record.id, raise_exception=False,force_send=True)

        for d in res:
            if d.after_date_days:
                if int(d.after_date_days) > 0 and int(d.after_date_days) < 11:
                    d.lb_green = True
                    d.lb_yellow = False
                    d.lb_red = False
                else:
                    if int(d.after_date_days) >=11 and int(d.after_date_days) <=20:
                        d.lb_green = False
                        d.lb_yellow = True
                        d.lb_red = False
                    else:
                        d.lb_green = False
                        d.lb_yellow = False
                        d.lb_red = True


class CountryInheritInteco(models.Model):
    _inherit = 'res.country.state'

    def name_get(self):
        result = []
        for doc in self:
            result.append((doc.id, doc.code+' '+doc.name))
        return result


class DefaultInheritInteco(models.Model):
    _inherit = 'account.analytic.default'

    categ_default = fields.Many2one('product.category', string='Categoría de producto', tracking=True)


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'


    @api.onchange('product_id')
    def _onchange_phone_validation(self):
        _logging.info("DEF321==============")

        for record in self:
            if record.product_id:
                if record.product_id.product_tmpl_id.product_analytic_account:
                    an_account = record.product_id.product_tmpl_id.product_analytic_account
                    record.analytic_account_id = an_account
                else:
                    if record.product_id.product_tmpl_id.categ_id.analytic_account_def:
                        an_account = record.product_id.product_tmpl_id.categ_id.analytic_account_def
                        record.analytic_account_id = an_account
                    else:
                        record.analytic_account_id = ''
            else:
                record.analytic_account_id = ''
