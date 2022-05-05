# -*- coding: utf-8 -*-
import traceback

from odoo import models, fields, api, http, _
from datetime import datetime, timedelta
from pytz import timezone
from odoo.http import request
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from dateutil.parser import parse
from odoo.tools.float_utils import float_is_zero
from itertools import groupby

class PurchaseOrderInherit(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'portal.mixin']
    _description = 'Solicitud de Presupuesto'

    # pdi = purchase_done_id
    purchase_done_id = fields.Selection(string="¿El gasto ya fue realizado?", selection=[
        ('pdi_yes', 'Si'),
        ('pdi_no', 'No')
    ], tracking=True)
    # cci = company_card_id
    company_card_id = fields.Selection(string="Tarjeta de INTECO", selection=[
        ('cci_yes', 'Si'),
        ('cci_no', 'No')
    ], tracking=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Petición presupuesto'),
            ('sent', 'Petición de presupuesto enviado'),
            ('to approve', 'Para aprobar'),
            ('final approve', 'Aprobación Final'),
            ('liquidate', 'Pendiente por liquidar'),
            ('doc_liquidate', 'Pendiente documentos'),
            ('purchase', 'Pedido comprado'),
            ('done liquidate', 'Liquidado'),
            ('ready_prov', 'Provision lista'),
            # ('to validate', 'Por Validar'),
            ('done', 'Bloqueado'),
            ('cancel', 'Cancelada'),
            # ('deposit', 'Depositado'),
            # ('pending docs', 'Pendiente documentos físicos'),
            # ('approved', 'Aprobado'),
            # ('pending', 'Pendiente'),
            # ('rejected', 'Rechazado')
        ],
    )
    invoice_status = fields.Selection(
        selection=[
            ('no', 'Nada para facturar'),
            ('no_val', 'Sin validación'),
            ('to invoice', 'Por Validar'),
            ('invoiced', 'Sin factura para recibir'),
            ('approved', 'Aprobado'),
            ('pending', 'Pendiente'),
            ('deposit', 'Depositado'),
            ('docs_pending', 'Pendiente documentos físicos'),
            ('rejected', 'Rechazado'),
        ],
    )
    approved_state = fields.Char(string="verde", invisible="1")
    cancel_state = fields.Char(string="rojo", invisible="1")
    number = fields.Char(string="number")

    requested_by = fields.Many2one('res.users',string="Solicitante", readonly=True, store="True", default=lambda self: self.env.user)
    requested_by_mail = fields.Char(string="correo del solicitador", readonly=True, store="True")

    approved_by = fields.Many2one('res.users', string="Primer Aprobador", readonly=True, store="True")
    approved_by_bk = fields.Many2one('res.users', string="Primer Aprobador(Backup)", readonly=True, store="True")
    approved_by_mail = fields.Char(string="correo del aprobador 1", readonly=True, store="True")
    approved_by_status = fields.Char(string="Estado Primer Aprobador", store="True", readonly=True)
    approved_by_status_3 = fields.Char(string="Estado Primer Aprobador 3 dias", store="True", readonly=True)
    approved_by_result = fields.Char(string='-', store="True", readonly=True)

    approved_by2 = fields.Many2one('res.users', string="Segundo Aprobador", store="True", readonly=True)
    approved_by2_mail = fields.Char(string="correo del aprobador 2", readonly=True, store="True")
    approved_by2_status = fields.Char(string="Estado Segundo Aprobador", store="True", readonly=True)
    approved_by2_status_3 = fields.Char(string="Estado Segundo Aprobador 3 dias", store="True", readonly=True)
    approved_by2_result = fields.Char(string='-', store="True", readonly=True)

    appr_datetime = fields.Datetime(string="Fecha de inicio", store="True")
    end_datetime = fields.Datetime(string="Fecha de finalización", store="True")
    deposit_date = fields.Datetime(string="Fecha de Deposito", store="True", tracking=True)
    payment_ref = fields.Char(string="Referencia de Deposito", store="True", tracking=True)
    approved_by_datetime = fields.Datetime(string="Fecha de inicio", store="True")
    approved_by_datetime3 = fields.Datetime(string="Fecha actual mas 3 días", store="True", readonly=True)
    approved_by_datetime7 = fields.Datetime(string="Fecha actual mas 7 días", store="True", readonly=True)

    purchase_notes = fields.Char(string="Estado",readonly=True)

    approv_req = fields.Boolean(string="¿Requiere liquidación?", tracking=True)
    expense_prov = fields.Boolean(string="Provisión de Gasto", tracking=True)
    advance_pur = fields.Boolean(string="Anticipo", tracking=True)
    approv_followers = fields.Boolean(string="Followers?")
    amount_to_pay = fields.Monetary(string="Suma adelantada", tracking=True)
    employee_name = fields.Many2one(comodel_name='res.users', string="Nombre del Empleado", store="True")
    employees_name = fields.Many2one(comodel_name='res.partner', string="Nombre del Empleado", store="True")
    employee_name_mail = fields.Char(string="Correo del Empleado", store="True")
    emp_amount_to_pay = fields.Monetary(string="Total de Gastos", tracking=True)
    amount_to_refund = fields.Monetary(string="Reintegro/Devolución", compute='check_amount_refund',  store=True, tracking=True)
    # state = fields.Selection(selection_add=[
    #     ('final approve','Aprobación Final','Pendiente por liquidar')
    # ])
    motive = fields.Char(string="motivo")
    purchase_record = fields.Char(string='Registro')
    purchase_version = fields.Char(string='Número de versión')
    current_user = fields.Boolean(compute='_current_user', store=False)
    liq_current_user = fields.Boolean(compute='_liq_current_user', store=False)
    file_check = fields.Boolean(compute='check_purchase_adj', store=False)
    req_current_user = fields.Boolean(compute='_1current_user', store=False)
    origin = fields.Char(compute='check_purchase_adj')
    doc_quant = fields.Char(string='Cantidad de Adjuntos(numero)', compute='check_purchase_adj')
    country_exp = fields.Boolean(string='¿Gasto aplicable a RD?', tracking=True)
    exp_country = fields.Char(string='Pais del Gasto', compute='_getCountry', store=True)
    view_country = fields.Char(string='Pais del Gasto', compute='_getCountry', store=True)
    depo_val = fields.Boolean(string='Depositado')
    depo_values = fields.Boolean(string='Depositado?')
    up_invoice = fields.Boolean(string='¿Posee Facturas?', tracking=True)
    del_invoice = fields.Datetime(string='¿Entrega de la Factura?', tracking=True)
    approved_by_date = fields.Datetime(string="Fecha de primera aprobación", store="True")
    approved_by2_date = fields.Datetime(string="Fecha de segunda aprobación", store="True")

    # metodo para ocultar campos cuando el usuario logeado es igual al usuario aprobador 1 o el respaldo del aprobador 1
    def _current_user(self):
        me = self.env.user.id
        if me == self.approved_by.id:
            self.current_user = True
        else:
            if me == self.approved_by_bk.id:
                self.current_user = True
            else:
                if me != self.approved_by2.id:
                    self.current_user = True
                else:
                    self.current_user = False


    # metodo para ocultar campos cuando el usuario logeado es igual al campo Nombre del Empleado
    def _liq_current_user(self):
        me = self.env.user.id
        if self.employees_name:
            user_part_id = self.env['res.users'].search([('partner_id', '=', self.employees_name.id)])
            if me == user_part_id.id:
                self.liq_current_user = True
            else:
                self.liq_current_user = False
        else:
            self.liq_current_user = False

    # metodo para ocultar campos cuando el usuario logeado es igual al usuario solicitador o el aprobador 2
    def _1current_user(self):
        me = self.env.user.id
        if me == self.requested_by.id:
            self.req_current_user = True
        else:
            if me == self.approved_by2.id:
                self.req_current_user = True
            else:
                if me == self.approved_by.id:
                    self.req_current_user = False
                else:
                    self.req_current_user = True

    #@api.multi
    @api.onchange('country_exp')
    def _getCountry(self):
        for record in self:
            if record.country_exp == True:
                record.exp_country = 'RD'
            else:
                record.exp_country = 'CR'

    #@api.multi
    @api.onchange('advance_pur')
    def _calcdeldate(self):
        for record in self:
            if record.advance_pur == True:
                record.del_invoice = record.end_datetime

    @api.onchange('exp_country')
    def _viewCountr(self):
        for record in self:
            record.view_country = record.exp_country

    @api.onchange('purchase_done_id')
    def _checkpur(self):
        for record in self:
            if record.purchase_done_id == 'pdi_yes':
                record.up_invoice = True


    #@api.multi
    @api.depends('amount_to_pay','emp_amount_to_pay')
    def check_amount_refund(self):
        for record in self:
            if record.expense_prov == False:
                record.amount_to_refund = record.amount_to_pay - record.emp_amount_to_pay
            else:
                record.amount_to_refund = 0


    #Validación monto a liquidar por el empleado mayor al monto a liquidar
    # @api.onchange('emp_amount_to_pay')
    # def check_monto(self):
    #     for record in self:
    #         if record.emp_amount_to_pay > record.amount_to_pay:
    #             raise Warning(
    #                 _('El monto a liquidar por el empleado no puede ser mayor al monto a liquidar'))


    #@api.multi
    def check_purchase_adj(self):
        for record in self:
            pur_id = record.id
            pur_orse = len(self.env['ir.attachment'].search([('res_id', '=', pur_id), ('res_model', '=', 'purchase.order')]))
            if pur_orse > 0:
                if record.up_invoice == True:
                    record.file_check = True
                    record.origin = 'Si'+' '+'('+str(pur_orse)+')'+' '+'Con Facturas'
                    record.doc_quant = pur_orse
                else:
                    record.file_check = True
                    record.origin = 'Si' + ' ' + '(' + str(pur_orse) + ')' + ' ' + 'Sin Facturas'
                    record.doc_quant = pur_orse
            else:
                record.file_check = False
                record.origin = 'No'
                record.doc_quant = pur_orse


    # metodo para mostrar los correos y nombres de los aprobadores(#1,#1(bk) y #2) dependiendo del usuario solicitante
    @api.onchange('requested_by')
    def get_users(self):
        # self.requested_by = self.env.user.name
        self.requested_by_mail = self.env.user.partner_id.email
        approvals = self.env['user.approval'].search([('user_requester', '=', self.env.user.id)])
        self.approved_by = approvals.user_approb1.id
        self.approved_by_bk = approvals.user_approb1_bk.id
        self.approved_by2 = approvals.user_approb2.id
        self.approved_by_mail = approvals.user_approb1.email
        self.approved_by2_mail = approvals.user_approb2.email

    @api.onchange('partner_id')
    def check_employee(self):
        for record in self:
            record.employees_name = record.partner_id.id

    # evento en el boton validar del solicitante
    #@api.multi
    def button_validate(self):
        today = datetime.now()
        pur_id = self.id
        pur_orse = len(
            self.env['ir.attachment'].search([('res_id', '=', pur_id), ('res_model', '=', 'purchase.order')]))
        if self.approved_by or self.approved_by2:
            pass
        else:
            raise ValidationError(
                _('Alerta, no puede validar un presupuesto sin todos los Aprobadores.'))
        if self.end_datetime < today and self.approv_req == True:
            raise ValidationError(
                _('Alerta, la Fecha de finalización no debe ser menor al dia actual.'))
        else:
            if pur_orse <= 0 or pur_orse == '':
                raise ValidationError(
                    _('Alerta, no puede validar la solicitud si nó adjunta algún documento'))
            else:
                if self.approv_req is True and self.amount_to_pay != self.amount_total:
                    raise ValidationError(
                        _('Alerta, La suma adelantada no puede ser diferente al monto total de la orden de compra!'))
                else:
                    if self.end_datetime < self.appr_datetime:
                        raise ValidationError(
                            _('Alerta, la Fecha de finalización no debe ser menor a la Fecha de inicio.'))
                    else:
                        if self.amount_total == 0:
                            raise ValidationError(
                                _('Alerta, el monto de la PO no puede ser 0.'))
                        else:
                            self.write({
                                'state': 'to approve',
                            })
                            self.write({
                                'invoice_status': 'no_val',
                            })
            if self.country_exp == True:
                self.exp_country = 'RD'
            else:
                self.exp_country = 'CR'
            self.depo_values = False
            self.purchase_notes = 'Pendiente por aprobación #1.'
            self.requested_by = self.env.user.id
            self.requested_by_mail = self.env.user.partner_id.email

            approvals = self.env['user.approval'].search([('user_requester', '=', self.env.user.id)])
            self.approved_by = approvals.user_approb1.id
            self.approved_by_mail = approvals.user_approb1.email
            self.approved_by2 = approvals.user_approb2.id
            self.approved_by2_mail = approvals.user_approb2.email
            self.approved_by_bk = approvals.user_approb1_bk.id

            email_template = self.env.ref('dfx_budget_request.purchase_email_template')
            email_template.email_to = self.approved_by_mail
            email_template.send_mail(self.id, raise_exception=False, force_send=True)
            self.approved_by_status = 'False'
            self.approved_by_status_3 = 'False'
            self.date_order = today
            cal = self.env['time.calc.funtions']
            self.approved_by_datetime3 = cal.cal_bussines_date(today,72)
            self.approved_by_datetime7 = cal.cal_bussines_date(today,168)
            self.approved_by_result = ''
            self.approved_by2_result = ''
            self.approved_by_date = ''
            self.approved_by2_date = ''
            if self.approv_req == True:
                foll = self.update_follower()
                if foll:
                    self.write({'message_follower_ids': foll})
                self.approv_followers = True

    #@api.multi
    def button_accept_liq(self):
        if self.emp_amount_to_pay != 0.00:
            if self.emp_amount_to_pay > self.amount_to_pay:
                view_id = self.env['exceed.wizard']
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Alerta',
                    'res_model': 'exceed.wizard',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('dfx_budget_request.emp_amount_pay_wizard', False).id,
                    'target': 'new',
                }
            else:
                emp_id = self.env['res.partner'].search([('id', '=', self.employees_name.id)])
                user_part_id = self.env['res.users'].search([('partner_id', '=', self.employees_name.id)])
                id_pur_model = self.env['ir.model'].search([('model', '=', 'purchase.order')])
                self.employee_name_mail = emp_id.email
                if self.employee_name_mail != '':
                    self.write({
                        'state': 'done liquidate'
                    })
                    self.write({
                        'state': 'ready_prov'
                    })
                    self.write({
                        'invoice_status': 'to invoice'
                    })
                    emp_id = self.env['res.partner'].search([('id', '=', self.employees_name.id)])
                    pur_act = self.env['mail.activity'].search([('res_id', '=', self.id)])
                    pur_act.action_feedback(feedback="Actividad hecha")
                    email_template = self.env.ref('dfx_budget_request.accept_email_template')
                    email_template.email_to = self.employee_name_mail
                    email_template.send_mail(self.id, raise_exception=False, force_send=True)
                    if user_part_id:
                        activity_type_id = self.env['mail.activity.type'].search([('name','=','Pendiente documentos de liquidación')])
                        if not activity_type_id:
                            msg = "Error: No se encuentra la actividad: Pendiente documentos de liquidación\nAgregar en Ajustes/Tipos de Actividad"
                            raise ValidationError( _(msg) )
                        self.env['mail.activity'].create({
                            'user_id': user_part_id.id,
                            'res_model_id': id_pur_model.id,
                            'note': 'Pendiente documentos de provisión:',
                            'date_deadline': self.end_datetime,
                            'activity_type_id': activity_type_id.id, #25 Pendiente documentos de liquidación,
                            'recommended_activity_type_id': False,
                            'res_id': self.id,
                            'summary': 'Pendiente documentos de provisión'})
                else:
                    raise Warning(
                        _('El empleado no posee correo electrónico, Favor modificarlo'))
        else:
            raise Warning(
                _('El monto a liquidar por el empleado no puede ser 0'))


    # metodo para obtener la direccion url de la PO actual
    def get_mail_url(self):
        return self._get_share_url(redirect=True)

    # metodo para obtener la direccion url de la PO mas reciente
    def get_latest_mail_url(self):
        last_id = self.env['purchase.order'].search([], order='id desc')[0]
        return last_id._get_share_url(redirect=True)

    # metodo para obtener el nombre de la PO mas reciente
    def get_latest_po_name(self):
        last_id = self.env['purchase.order'].search([], order='id desc')[0]
        return last_id.name


    #@api.multi
    def button_cancel_first(self):
        view_id = self.env['purchase1.wizard']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerta : Cancelación de solicitud de presupuesto',
            'res_model': 'purchase1.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_budget_request.my_cancel_email_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def button_liq_cancel(self):
        self.write({
            'state': 'cancel',
        })

    # evento en el boton cancelar para utilizar el wizard(pop up)
    #@api.multi
    def button_cancel(self):
        nomb = self.env.user.name
        self.approved_by2_result = str(nomb + ' ' + 'denegado')
        view_id = self.env['purchase1.wizard']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerta : Cancelación de solicitud de presupuesto',
            'res_model': 'purchase1.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_budget_request.my_cancel_email_wizard', False).id,
            'target': 'new',
        }

    # evento en el boton aprobar
    #@api.multi
    def button_approve(self):
        nomb = self.env.user.name
        self.approved_by_result = str(nomb + ' ' + 'Aprobado')
        self.approved_by_date = datetime.now()
        self.write({
            'state': 'final approve',
        })
        self.write({
            'invoice_status': 'no_val',
        })
        self.purchase_notes = 'Pendiente por aprobación #2.'
        email_template = self.env.ref('dfx_budget_request.purchase_email_template')
        email_template.email_to = self.approved_by2_mail
        email_template.send_mail(self.id, raise_exception=False, force_send=True)

        self.approved_by_status = 'True'
        self.approved_by2_status = 'False'
        self.approved_by2_status_3 = 'False'
        self.purchase_notes = ''
        today = datetime.now()
        cal = self.env['time.calc.funtions']
        self.approved_by_datetime3 = cal.cal_bussines_date(today, 72)
        self.approved_by_datetime7 = cal.cal_bussines_date(today, 168)
        if self.approv_req == True and self.approv_followers == False:
            foll = self.update_follower()
            if foll:
                self.write({'message_follower_ids': foll})
                self.approv_followers = True

    def update_follower(self):
        followers = []
        # for follower in self.message_follower_ids.filtered(lambda x: x.partner_id == ):
        # followers.append([2, follower.id])
        if self.employees_name and self.employees_name not in self.message_follower_ids.mapped('partner_id'):
            followers.append([0, 0, {'partner_id': self.employees_name.id,
                                     'subtype_ids': [(6, 0, [1, 3])],
                                     'res_model': 'purchase.order'}])
        return followers

    # def update_followers(self):
    #     followers = []
    #     for p_id:
    #         if p_id not in self.message_follower_ids.mapped('partner_id') \
    #                 and p_id != self.env['res.users'].browse(self._uid).partner_id:
    #             followers.append([0, 0, {'partner_id': self.employee_name.id,
    #                                      'subtype_ids': [(6, 0, [1, 3])],
    #                                      'res_model': 'purchase.order'}])
    #     return followers

    # evento en el botón confirmar
    #@api.multi
    def button_confirm(self):
        nomb = self.env.user.name
        self.approved_by2_result = str(nomb + ' ' + 'Aprobado')
        self.purchase_notes = 'Solicitud aprobada.'
        self.approved_by2_date = datetime.now()
        email_template = self.env.ref('dfx_budget_request.accept_email_template')
        email_template.email_to = self.requested_by_mail
        email_template.send_mail(self.id, raise_exception=False, force_send=True)
        user_part_id = self.env['res.users'].search([('partner_id', '=', self.employees_name.id)])
        if self.approv_req == True and self.approv_followers == True:
            # check de Provisión de Gasto activado
            if self.expense_prov is True:
                self.write({
                    'state': 'liquidate'
                })
                self.write({
                    'invoice_status': 'no_val'
                })

                # us_name = self.env.user.name
                today = datetime.now()
                cal = self.env['time.calc.funtions']
                id_pur_model = self.env['ir.model'].search([('model', '=', 'purchase.order')])
                if user_part_id:
                    activity_type_id = self.env['mail.activity.type'].search([('name','=','Pendiente documentos de liquidación')])
                    if not activity_type_id:
                        msg = "Error: No se encuentra la actividad: Pendiente documentos de liquidación\nAgregar en Ajustes/Tipos de Actividad"
                        raise ValidationError( _(msg) )
                    self.env['mail.activity'].create({
                        'user_id': user_part_id.id,
                        'res_model_id': id_pur_model.id,
                        'note': 'Pendiente documentos de provisión:',
                        'date_deadline': cal.cal_bussines_date(self.end_datetime, 120),
                        'activity_type_id': activity_type_id.id, #25 Pendiente documentos de liquidación,
                        'recommended_activity_type_id': False,
                        'res_id': self.id,
                        'summary': 'Pendiente documentos de provisión'})
                else:
                    self.employees_name = ''
                    raise ValidationError(
                        _('Alerta, la persona que debe realizar la liquidación debe ser un funcionario.'))
            else:
                # check de anticipo activado
                if self.advance_pur is True:
                    self.write({
                        'state': 'liquidate'
                    })
                    self.write({
                        'invoice_status': 'no_val'
                    })
                    # us_name = self.env.user.name
                    today = datetime.now()
                    cal = self.env['time.calc.funtions']
                    id_pur_model = self.env['ir.model'].search([('model', '=', 'purchase.order')])
                    if user_part_id:
                        activity_type_id = self.env['mail.activity.type'].search([('name','=','Pendiente anticipo')])
                        if not activity_type_id:
                            msg = "Error: No se encuentra la actividad: Pendiente anticipo\nAgregar en Ajustes/Tipos de Actividad"
                            raise ValidationError( _(msg) )
                        self.env['mail.activity'].create({
                            'user_id': user_part_id.id,
                            'res_model_id': id_pur_model.id,
                            'note': 'Pendiente anticipo:',
                            'date_deadline': cal.cal_bussines_date(self.end_datetime, 120),
                            'activity_type_id': activity_type_id.id, #26 Pendiente anticipo,
                            'recommended_activity_type_id': False,
                            'res_id': self.id,
                            'summary': 'Pendiente anticipo'})
                    else:
                        self.employees_name = ''
                        raise ValidationError(
                            _('Alerta, la persona que debe realizar la liquidación debe ser un funcionario.'))
                else:
                    self.write({
                        'state': 'doc_liquidate'
                    })
                    self.write({
                        'invoice_status': 'no_val'
                    })
                    # us_name = self.env.user.name
                    today = datetime.now()
                    cal = self.env['time.calc.funtions']
                    id_pur_model = self.env['ir.model'].search([('model', '=', 'purchase.order')])
                    if user_part_id:
                        self.env['mail.activity'].create({
                            'user_id': user_part_id.id,
                            'res_model_id': id_pur_model.id,
                            'note': 'Monto:' + ' ' + str(round(self.amount_to_pay, 2)) + ' ' + 'Moneda:' + ' ' + self.currency_id.name,
                            'date_deadline': cal.cal_bussines_date(today, 120),
                            'activity_type_id': self.env.user.company_id.mail_activity_purchase.id,
                            'recommended_activity_type_id': False,
                            'res_id': self.id,
                            'summary': 'Pendiente por liquidar'})
                    else:
                        self.employees_name = ''
                        raise ValidationError(
                            _('Alerta, la persona que debe realizar la liquidación debe ser un funcionario.'))

            email_template = self.env.ref('dfx_budget_request.liqui_approved_email_template')
            email_template.email_to = self.approved_by_mail
            email_template.send_mail(self.id, raise_exception=False, force_send=True)
        else:
            if self.approv_req == True and self.approv_followers == False:
                if self.expense_prov is True:
                    self.write({
                        'state': 'liquidate'
                    })
                    self.write({
                        'invoice_status': 'no_val'
                    })
                    foll = self.update_follower()
                    self.write({'message_follower_ids': foll})
                    self.approv_followers = True

                    # us_name = self.env.user.name
                    today = datetime.now()
                    cal = self.env['time.calc.funtions']
                    id_pur_model = self.env['ir.model'].search([('model','=','purchase.order')])
                    if user_part_id:
                        activity_type_id = self.env['mail.activity.type'].search([('name','=','Pendiente documentos de liquidación')])
                        if not activity_type_id:
                            msg = "Error: No se encuentra la actividad: Pendiente documentos de liquidación\nAgregar en Ajustes/Tipos de Actividad"
                            raise ValidationError( _(msg) )
                        self.env['mail.activity'].create({
                            'user_id': user_part_id.id,
                            'res_model_id': id_pur_model.id,
                            'note': 'Pendiente documentos de provisión:',
                            'date_deadline': cal.cal_bussines_date(self.end_datetime, 120),
                            'activity_type_id': activity_type_id.id, # 25 Pendiente documentos de liquidación,
                            'recommended_activity_type_id': False,
                            'res_id': self.id,
                            'summary': 'Pendiente documentos de provisión'})
                    else:
                        self.employees_name = ''
                        raise ValidationError(
                            _('Alerta, la persona que debe realizar la liquidación debe ser un funcionario.'))
                else:
                    if self.advance_pur is True:
                        self.write({
                            'state': 'liquidate'
                        })
                        self.write({
                            'invoice_status': 'no_val'
                        })
                        foll = self.update_follower()
                        self.write({'message_follower_ids': foll})
                        self.approv_followers = True

                        # us_name = self.env.user.name
                        today = datetime.now()
                        cal = self.env['time.calc.funtions']
                        id_pur_model = self.env['ir.model'].search([('model','=','purchase.order')])
                        if user_part_id:
                            activity_type_id = self.env['mail.activity.type'].search([('name','=','Pendiente anticipo')])
                            if not activity_type_id:
                                msg = "Error: No se encuentra la actividad: Pendiente anticipo\nAgregar en Ajustes/Tipos de Actividad"
                                raise ValidationError( _(msg) )
                            self.env['mail.activity'].create({
                                'user_id': user_part_id.id,
                                'res_model_id': id_pur_model.id,
                                'note': 'Pendiente anticipo:',
                                'date_deadline': cal.cal_bussines_date(self.end_datetime, 120),
                                'activity_type_id': activity_type_id.id, #26 Pendiente anticipo,
                                'recommended_activity_type_id': False,
                                'res_id': self.id,
                                'summary': 'Pendiente anticipo'})
                        else:
                            self.employees_name = ''
                            raise ValidationError(
                                _('Alerta, la persona que debe realizar la liquidación debe ser un funcionario.'))
                    else:
                        self.write({
                            'state': 'doc_liquidate'
                        })
                        self.write({
                            'invoice_status': 'no_val'
                        })
                        foll = self.update_follower()
                        self.write({'message_follower_ids': foll})
                        self.approv_followers = True

                        # us_name = self.env.user.name
                        today = datetime.now()
                        cal = self.env['time.calc.funtions']
                        id_pur_model = self.env['ir.model'].search([('model','=','purchase.order')])
                        if user_part_id:
                            self.env['mail.activity'].create({
                                'user_id': user_part_id.id,
                                'res_model_id':id_pur_model.id,
                                'note':'Monto:'+' '+str(round(self.amount_to_pay, 2))+' '+'Moneda:'+' '+self.currency_id.name,
                                'date_deadline': cal.cal_bussines_date(today, 120),
                                'activity_type_id':self.env.user.company_id.mail_activity_purchase.id,
                                'recommended_activity_type_id':False,
                                'res_id': self.id,
                                'summary':'Pendiente por liquidar'})
                        else:
                            self.employees_name = ''
                            raise ValidationError(
                                _('Alerta, la persona que debe realizar la liquidación debe ser un funcionario.'))

                email_template = self.env.ref('dfx_budget_request.liqui_approved_email_template')
                email_template.email_to = self.approved_by_mail
                email_template.send_mail(self.id, raise_exception=False, force_send=True)

            else:
                if self.approv_req == False and self.approv_followers == False:
                    self.write({
                        'state': 'purchase',
                    })
                    self.write({
                        'invoice_status': 'to invoice'
                    })
                    for order in self:
                        if order.state not in ['draft', 'sent']:
                            continue
                        order._add_supplier_to_product()
                        # Deal with double validation process
                        if order.company_id.po_double_validation == 'one_step' \
                                or (order.company_id.po_double_validation == 'two_step' \
                                    and order.amount_total < self.env.company.currency_id._convert(
                                    order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                                    order.date_order or fields.Date.today())) \
                                or order.user_has_groups('purchase.group_purchase_manager'):
                            order.button_approve()
                        else:
                            order.write({'state': 'to approve'})
                        if order.partner_id not in order.message_partner_ids:
                            order.message_subscribe([order.partner_id.id])
                    return True
                else:
                    if self.approv_req == False and self.approv_followers == True:
                        self.write({
                            'state': 'purchase',
                        })
                        self.write({
                            'invoice_status': 'to invoice'
                        })
                        for order in self:
                            if order.state not in ['draft', 'sent']:
                                continue
                            order._add_supplier_to_product()
                            # Deal with double validation process
                            if order.company_id.po_double_validation == 'one_step' \
                                    or (order.company_id.po_double_validation == 'two_step' \
                                        and order.amount_total < self.env.company.currency_id._convert(
                                        order.company_id.po_double_validation_amount, order.currency_id,
                                        order.company_id,
                                        order.date_order or fields.Date.today())) \
                                    or order.user_has_groups('purchase.group_purchase_manager'):
                                order.button_approve()
                            else:
                                order.write({'state': 'to approve'})
                            if order.partner_id not in order.message_partner_ids:
                                order.message_subscribe([order.partner_id.id])
                        return True

        self.approved_by2_status = 'True'
        self.approved_by2_status_3 = ''

    @api.onchange('requested_by')
    def calc_end_date(self):
        today1 = datetime.now()
        cal = self.env['time.calc.funtions']
        self.appr_datetime = today1
        self.end_datetime = cal.cal_bussines_date(today1, 120)

    @api.model
    def check_date_notapp(self):
        rec = self.env['purchase.order'].search([])
        for record in rec:
            date_today = datetime.now()
            record.approved_by_datetime = date_today

            if record.approved_by_status == 'False' and record.approved_by_datetime >= record.approved_by_datetime3 and record.approved_by_status_3 == 'False':
                record.purchase_notes = 'Bloqueo por tiempo de aprobación'
                record.approved_by_status_3 = 'True'
            else:
                if record.approved_by_status == 'False' and record.approved_by_datetime >= record.approved_by_datetime7 and record.approved_by_status_3 == 'True':
                    record.write({
                        'state': 'done'
                    })
                    record.purchase_notes = 'Bloqueo por tiempo de aprobación'+' '+ str(record.approved_by_datetime7)
                    record.approved_by_status_3 = 'N/A'
                else:
                    if record.approved_by2_status == 'False' and record.approved_by_datetime >= record.approved_by_datetime3 and record.approved_by2_status_3 == 'False':
                        record.purchase_notes = 'Bloqueo por tiempo de aprobación'
                        record.approved_by2_status_3 == 'True'
                    else:
                        if record.approved_by2_status == 'False' and record.approved_by_datetime >= record.approved_by_datetime7 and record.approved_by2_status_3 == 'True':
                            record.write({
                                'state': 'done'
                            })
                            record.purchase_notes = 'Bloqueo por tiempo de aprobación' + ' ' + str(record.approved_by_datetime7)
                            record.approved_by2_status_3 = 'N/A'
                        else:
                            pass

    @api.model
    def invoice_reminder(self):
        rec = self.env['purchase.order'].search([])
        today = datetime.now()
        cal = self.env['time.calc.funtions']
        for record in rec:
            if record.up_invoice is not True and record.state == ('purchase', 'liquidate') and record.del_invoice:
                f_day = cal.cal_bussines_date(record.del_invoice, 24)
                s_day = cal.cal_bussines_date(record.del_invoice, 48)
                if today <= f_day:
                    email_template = self.env.ref('dfx_budget_request.reminder_invoice_email_template')
                    email_template.email_to = record.requested_by_mail
                    email_template.send_mail(record.id, raise_exception=False, force_send=True)
                else:
                    if today <= s_day:
                        email_template = self.env.ref('dfx_budget_request.reminder_invoice_email_template')
                        email_template.email_to = record.requested_by_mail
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                    else:
                        if today <= record.del_invoice:
                            activity_type_id = self.env['mail.activity.type'].search([('name','=','Pendiente subir facturas')])
                            if not activity_type_id:
                                msg = "Error: No se encuentra la actividad: Pendiente subir facturas\nAgregar en Ajustes/Tipos de Actividad"
                                raise ValidationError( _(msg) )
                            # user_part_id = self.env['res.users'].search([('partner_id', '=', record.employees_name.id)])
                            id_pur_model = self.env['ir.model'].search([('model', '=', 'purchase.order')])
                            self.env['mail.activity'].create({
                                'user_id': record.requested_by.id,
                                'res_model_id': id_pur_model.id,
                                'note': 'Monto:',
                                'date_deadline': cal.cal_bussines_date(record.del_invoice, 48),
                                'activity_type_id': activity_type_id.id, #24 Pendiente subir facturas,
                                'recommended_activity_type_id': False,
                                'res_id': record.id,
                                'summary': 'Recordatorio de subir facturas'})

                            email_template = self.env.ref('dfx_budget_request.reminder_invoice_email_template')
                            email_template.email_to = record.requested_by_mail
                            email_template.send_mail(record.id, raise_exception=False, force_send=True)
                        else:
                            pass
            else:
                pass

    #@api.multi
    def button_appr_pur(self):
        self.message_post(body="Presupuesto Aprobado")
        self.write({
            'invoice_status': 'approved'
        })
        self.depo_values = True

        email_template = self.env.ref('dfx_budget_request.approve_email_template')
        email_template.email_to = self.requested_by_mail
        email_template.send_mail(self.id, raise_exception=False, force_send=True)

    #@api.multi
    def button_acc_dep(self):
        emp_id = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
        if emp_id.email:
            email_template = self.env.ref('dfx_budget_request.app_deposit_email_template')
            email_template.email_to = self.requested_by_mail+','+' '+emp_id.email
            email_template.send_mail(self.id, raise_exception=False, force_send=True)
            self.message_post(body="Fecha de depósito:" + " " + self.deposit_date+" "+"y Referencia de depósito:"+" "+self.payment_ref+" "+"agregados")
        else:
            raise Warning(
                _('El Proveedor/Funcionario no posee correo electrónico, Favor modificarlo'))


    #@api.multi
    def button_dep_pur(self):
        view_id = self.env['deposit.wizard']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerta',
            'res_model': 'deposit.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_budget_request.emp_deposit_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def button_pending_pur(self):
        view_id = self.env['pending.wizard']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerta : Presupuesto Pendiente',
            'res_model': 'pending.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_budget_request.my_pending_email_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def button_reject_pur(self):
        view_id = self.env['reject.wizard']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerta : Presupuesto Rechazado',
            'res_model': 'reject.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_budget_request.my_reject_email_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def button_confirm_pur(self):
        self.write({
            'state': 'to validate'
        })
        self.write({
            'invoice_status': 'to invoice'
        })

    def reassing_all(self):

        budget = {
            ('002','002 Servicios Especiales: servicios de seguridad'),
            ('005','005 Honorarios'),
            ('010','010 Otros Servicios Personales'),
            ('101','101 Alquileres'),
            ('104','104 Publicidad'),
            ('106','106 Impresión y encuadernación'),
            ('107','107 Telecomunicaciones'),
            ('110','110 Servicio de correo'),
            ('112','112 Gastos de viaje'),
            ('114','114 Gastos representación'),
            ('115','115 Gastos de transporte'),
            ('125','125 Mantenimiento y reparación de equipo de cómputo'),
            ('127','127 Mantenimiento y reparación mobiliario y equipo de oficina'),
            ('128','128 Mantenimiento y reparación de edificios'),
            ('204','204 Medicinas'),
            ('206','206 Impresos y Otros'),
            ('208','208 Productos alimenticios'),
            ('214','214 Materiales de oficina'),
            ('215','215 Materiales de limpieza'),
            ('230','230 Otros gastos (aquellos que no tengan un gasto definido)'),
            ('605','605 Capacitación de funcionarios'),
            ('607','607 Afiliaciones Internacionales'),
            ('121001','12-10-01 Compra de activos'),
            ('142017','14-20-17 CRM a Intangible'),
            ('142018','14-20-18 ERP a Intangible'),
            ('142019','14-20-19 WWW WEB Page a Intangibles'),
            ('142020','14-20-20 Ecomerce a Intangibles'),
            ('142021','14-20-21 BPM a Intangibles')
        }

        for bud in budget:
            self.env['budget.account'].sudo().create({'budget_name': bud[1]})

        cost = {
            ('09','09 Gastos Normalización'),
            ('10','10 Normalización'),
            ('20','20 Formación'),
            ('30','30 Venta de Normas'),
            ('40','40 Servicios de Certificación'),
            ('42','42 Alimentos'),
            ('45','45 GEI'),
            ('50','50 I+D+I'),
            ('51','51 Comunicación'),
            ('60','60 Servicios de Apoyo'),
            ('70','70 Producto'),
            ('80','80 Gestión de Sistemas'),
            ('81','81 Patrocinio')
        }

        for cos in cost:
            self.env['cost.center'].sudo().create({'cost_name': cos[1]})

    def reassing_cost_budget(self):
        all_purchase = self.env['purchase.order'].search([])

        for pur in all_purchase:

            for order_pur in pur.order_line:
                cost_name = dict(order_pur._fields['cost_center'].selection).get(order_pur.cost_center)
                search_cost = self.env['cost.center'].search([('cost_name', '=', cost_name)])
                if order_pur.cost_center and search_cost:
                    order_pur.new_cost_center = search_cost.id

                budget_name = dict(order_pur._fields['budget_account'].selection).get(order_pur.budget_account)
                search_budget = self.env['budget.account'].search([('budget_name', '=', budget_name)])
                if order_pur.budget_account and search_budget:
                    order_pur.new_budget_account = search_budget.id


    def button_fix_pur_invoice(self):
        all_purchase = self.env['purchase.order'].search([('state', '=', 'purchase')])

        for pur in all_purchase:

            for order in pur:
                if order.state not in ['draft', 'sent']:
                    continue
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step' \
                        or (order.company_id.po_double_validation == 'two_step' \
                            and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today())) \
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
                if order.partner_id not in order.message_partner_ids:
                    order.message_subscribe([order.partner_id.id])
            return True

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for order in self:
            if order.invoice_status != 'to invoice' and order.invoice_status != 'approved':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)


class Purchase_Order_Inherit(models.Model):
    _inherit = "purchase.order.line"
    _description = 'añadir campos al tree order line'

    cost_center = fields.Selection(selection=[
        ('09', '09 Gastos Normalización'),
        ('10','10 Normalización'),
        ('20','20 Formación'),
        ('30','30 Venta de Normas'),
        ('40','40 Servicios de Certificación'),
        ('42','42 Alimentos'),
        ('45','45 GEI'),
        ('50','50 I+D+I'),
        ('51','51 Comunicación'),
        ('60','60 Servicios de Apoyo'),
        ('70','70 Producto'),
        ('80','80 Gestión de Sistemas'),
        ('81','81 Patrocinio')], string="Centro de Costos",)

    budget_account = fields.Selection(selection=[
        ('002','002 Servicios Especiales: servicios de seguridad'),
        ('005','005 Honorarios'),
        ('010','010 Otros Servicios Personales'),
        ('101','101 Alquileres'),
        ('104','104 Publicidad'),
        ('106','106 Impresión y encuadernación'),
        ('107','107 Telecomunicaciones'),
        ('110','110 Servicio de correo'),
        ('112','112 Gastos de viaje'),
        ('114','114 Gastos representación'),
        ('115','115 Gastos de transporte'),
        ('125','125 Mantenimiento y reparación de equipo de cómputo'),
        ('127','127 Mantenimiento y reparación mobiliario y equipo de oficina'),
        ('128','128 Mantenimiento y reparación de edificios'),
        ('204','204 Medicinas'),
        ('206','206 Impresos y Otros'),
        ('208','208 Productos alimenticios'),
        ('214','214 Materiales de oficina'),
        ('215','215 Materiales de limpieza'),
        ('230','230 Otros gastos (aquellos que no tengan un gasto definido)'),
        ('605','605 Capacitación de funcionarios'),
        ('607','607 Afiliaciones Internacionales'),
        ('121001','12-10-01 Compra de activos'),
        ('142017','14-20-17 CRM a Intangible'),
        ('142018','14-20-18 ERP a Intangible'),
        ('142019','14-20-19 WWW WEB Page a Intangibles'),
        ('142020','14-20-20 Ecomerce a Intangibles'),
        ('142021','14-20-21 BPM a Intangibles')],string="Cuenta Presupuestaria")

    product_id = fields.Many2one(comodel_name="product.product", string="Producto")
    new_cost_center = fields.Many2one(comodel_name="cost.center", string="Centro de Costos")
    new_budget_account = fields.Many2one(comodel_name="budget.account", string="Cuenta Presupuestaria")


class PopUpEmailPurchase(models.TransientModel):
    _name = 'purchase1.wizard'
    _description = 'Pop up para poder insertar un mensaje en el correo electrónico'

    mail_info = fields.Char(string="Motivo de cancelación:")

    #@api.multi
    def cancel_button_email(self):
        record = self.env['purchase.order'].browse(self._context.get('active_id', []))
        nomb = self.env.user.name
        me = self.env.user.id
        emp_id = self.env['res.partner'].search([('id', '=', record.employees_name.id)])
        record.employee_name_mail = emp_id.email
        record.message_post(body="Motivo de cancelación:"+" "+self.mail_info)
        record.write({
            'state': 'cancel',
        })
        record.write({
            'state': 'draft',
        })
        record.approved_by_status = '1'
        record.approved_by2_status = '1'
        record.approved_by_result = str('')
        record.approved_by_date = ''
        record.approved_by2_date = ''
        record.approved_by2_result = str('')
        record.purchase_notes = str('Cancelado por:' + ' ' + nomb)
        if me == record.requested_by.id:
            if record.approv_req == True:
                record.motive = self.mail_info
                email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                    record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login) + ',' + ' ' + str(
                    record.employees_name.email)
                email_template.send_mail(record.id, raise_exception=False, force_send=True)
            else:
                record.motive = self.mail_info
                email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                    record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login)
                email_template.send_mail(record.id, raise_exception=False, force_send=True)
        else:
            if me == record.approved_by.id:
                if record.approv_req == True:
                    record.motive = self.mail_info
                    email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                    email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                        record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login) + ',' + ' ' + str(
                        record.employees_name.email)
                    email_template.send_mail(record.id, raise_exception=False, force_send=True)
                else:
                    record.motive = self.mail_info
                    email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                    email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                        record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login)
                    email_template.send_mail(record.id, raise_exception=False, force_send=True)
            else:
                if me == record.approved_by2.id:
                    if record.approv_req == True:
                        record.motive = self.mail_info
                        email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                        email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                            record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login) + ',' + ' ' + str(
                            record.employees_name.email)
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                    else:
                        record.approved_by_result = str('')
                        record.approved_by2_result = str('')
                        record.purchase_notes = str('Cancelado por:' + ' ' + nomb)
                        record.motive = self.mail_info
                        email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                        email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                            record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login)
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                else:
                    if record.approv_req == True:
                        record.motive = self.mail_info
                        email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                        email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                            record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login) + ',' + ' ' + str(
                            record.employees_name.email)
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)
                    else:
                        record.motive = self.mail_info
                        email_template = record.env.ref('dfx_budget_request.cancel_purchase_email_template')
                        email_template.email_to = str(record.requested_by.login) + ',' + ' ' + str(
                            record.approved_by.login) + ',' + ' ' + str(record.approved_by2.login)
                        email_template.send_mail(record.id, raise_exception=False, force_send=True)


class DepositPopUp(models.TransientModel):
    _name = 'deposit.wizard'
    _description = 'Pop up para mostrar un mensaje'

    #@api.multi
    def yes_dep_button(self):
        record = self.env['purchase.order'].browse(self._context.get('active_id', []))
        record.message_post(body="El empleado sí entregó los documentos originales de factura")
        record.write({
            'invoice_status': 'deposit'
        })
        record.depo_val = True
        record.depo_values = False

    #@api.multi
    def no_dep_button(self):
        record = self.env['purchase.order'].browse(self._context.get('active_id', []))
        record.message_post(body="El empleado nó entregó los documentos originales de factura")
        record.write({
            'invoice_status': 'docs_pending'
        })
        record.depo_values = False


class RejectPopUpEmail(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Pop up para poder insertar un mensaje en el correo electrónico'

    mail_info = fields.Char(string="Indique justificación del rechazo:")

    #@api.multi
    def reject_button_email(self):
        record = self.env['purchase.order'].browse(self._context.get('active_id', []))
        record.message_post(body="Presupuesto rechazado")
        record.write({
            'invoice_status': 'rejected'
        })
        record.motive = self.mail_info
        email_template = record.env.ref('dfx_budget_request.rejected_purchase_email_template')
        email_template.email_to = record.requested_by_mail
        email_template.send_mail(record.id, raise_exception=False, force_send=True)


class PendingPopUpEmail(models.TransientModel):
    _name = 'pending.wizard'
    _description = 'Pop up para poder insertar un mensaje en el correo electrónico'

    mail_info = fields.Char(string="Indique el pendiente:")

    #@api.multi
    def pending_button_email(self):
        record = self.env['purchase.order'].browse(self._context.get('active_id', []))
        record.message_post(body="Presupuesto pendiente")
        record.write({
            'invoice_status': 'pending'
        })
        record.motive = self.mail_info
        email_template = record.env.ref('dfx_budget_request.pending_purchase_email_template')
        email_template.email_to = record.requested_by_mail
        email_template.send_mail(record.id, raise_exception=False, force_send=True)


class ExceedPopUpEmail(models.TransientModel):
    _name = 'exceed.wizard'

    #@api.multi
    def exceed_button_email(self):
        today = datetime.now()
        cal = self.env['time.calc.funtions']
        record = self.env['purchase.order'].browse(self._context.get('active_id', []))
        emp_id = self.env['res.partner'].search([('id', '=', record.employees_name.id)])
        record.employee_name_mail = emp_id.email

        purchase_order_id = self.env['purchase.order'].create({
            'purchase_done_id': record.purchase_done_id,
            'company_card_id': record.company_card_id,
            'partner_id': record.partner_id.id,
            'currency_id': record.currency_id.id,
            'country_exp': record.country_exp,
            'requested_by': record.requested_by.id,
            'requested_by_mail': record.requested_by_mail,
            'approved_by': record.approved_by.id,
            'approved_by_mail': record.approved_by_mail,
            'approved_by2': record.approved_by2.id,
            'approved_by2_mail': record.approved_by2_mail,
            'date_order': record.date_order,
            'approv_req': record.approv_req,
            'expense_prov': record.expense_prov,
            'advance_pur': record.advance_pur,
            'amount_to_pay': (record.amount_to_refund*-1),
            'employees_name': record.employees_name.id,
            'appr_datetime': record.approved_by_datetime,
            'end_datetime': record.end_datetime,
            'state': 'to approve',
        })

        for rec in record.order_line:
            self.env['purchase.order.line'].create({
                'product_id': rec.product_id.id,
                'name': rec.name,
                'date_planned': rec.date_planned,
                'product_qty': rec.product_qty,
                'cost_center': rec.new_cost_center.id,
                'budget_account': rec.new_budget_account.id,
                'qty_received': rec.qty_received,
                'qty_invoiced': rec.qty_invoiced,
                'product_uom': rec.product_uom.id,
                'price_unit': rec.price_unit,
                'taxes_id': rec.taxes_id,
                'price_subtotal': rec.price_subtotal,
                'order_id': purchase_order_id.id
            })

        record.message_post(body="Presupuesto por Validar")
        record.write({
            'invoice_status': 'pending'
        })
        record.write({
            'state': 'done liquidate'
        })
        email_template = record.env.ref('dfx_budget_request.accept_email_template')
        email_template.email_to = record.requested_by_mail
        email_template.send_mail(record.id, raise_exception=False, force_send=True)

        last_id = self.env['purchase.order'].search([],order='id desc')[0]
        last_id.message_post(body="Esta solicitud del presupuesto fué creada a partir del:"+" "+record.name)
        email_template1 = record.env.ref('dfx_budget_request.latest_purchase_email_template')
        email_template1.email_to = record.requested_by_mail
        email_template1.send_mail(record.id, raise_exception=False, force_send=True)

class Purchase_Order_Attachment_Inherit(models.Model):
    _inherit = "ir.attachment"
    _description = 'añadir campos al tree order line'

    '''
    # @api.model
    def create(self, values):
        today = datetime.now().strftime('%Y-%m-%d')
        fmt = "%I:%M %p"
        # now_utc = datetime.now(timezone('UTC'))
        # now_pac = now_utc.astimezone(timezone(self.env.user.tz))
        # date_time = now_pac.strftime(fmt)
        res = super(Purchase_Order_Attachment_Inherit, self).create(values)
        if res.res_model and res.res_id and res.res_model == 'purchase.order':
            last_id = self.env['ir.attachment'].search([], order='id desc')[0]
            self.env[res.res_model].browse(res.res_id).message_post(body="Adjunto Agregado:"+" "+last_id.name+"<br/>"+"Fecha de creación:"+" "+today+"<br/>")
            # self.env[res.res_model].browse(res.res_id).message_post(body="Adjunto Agregado:"+" "+last_id.name+"<br/>"+"Fecha de creación:"+" "+today+"<br/>"+"Hora de creación:"+" "+str(date_time))
        return res
    '''
