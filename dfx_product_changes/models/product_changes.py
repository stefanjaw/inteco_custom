# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from itertools import groupby
DOMAIN = []
import logging

from odoo.exceptions import ValidationError

log = logging.getLogger(__name__)

class ProductInternCatInherit(models.Model):
    _inherit = "product.template"
    _description = 'añadir campos al tree order line'

    # type = fields.Selection([
    #     ('consu', 'Consumable'),
    #     ('service', 'Service'),
    #     ('product', 'Almacenable')], string='Product Type', default='consu', required=True)
    attribute_value_ids = fields.Many2many(
        'product.attribute.value', string='Attribute Values', ondelete='restrict')
    categ_id = fields.Many2one(comodel_name="product.category", string="Categoría Interna", required=False)
    categ_id_name = fields.Char(related="categ_id.name", string="Nombre de la Categoría" invisible=True)
    new_replaced_by = fields.Many2one(comodel_name="product.template", string="Nuevo Sustituido por", required=False)
    key_words = fields.Many2many(comodel_name="prod.key.words", string='Palabras Clave')
    course_duration = fields.Integer(string='Duración del Curso')
    is_cor = fields.Boolean(string='Es COR/ENM?', compute="is_cor_enm")
    is_enm = fields.Boolean(string='es norma?', store=False, compute="field_def_exp")
    default_type = fields.Char(string='Tipo')
    course_req = fields.Char(string='Requisitos del Curso')
    edition_con = fields.Integer(string='Consecutivo')
    mod_type = fields.Selection([
        ('mod', 'Modificada'),
        ('partial', 'Parcial'),
        ('iden', 'Idéntica'),
        ('None_type', 'N/A')
    ], string='Tipo de modificación')

    def is_cor_enm(self):
        for record in self:
            if record.default_code:
                if record.default_code.find("ENM") >= 0 or record.default_code.find("COR") >= 0:
                    record.is_cor = True
                else:
                    record.is_cor = False
            else:
                record.is_cor = False

    #@api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = self.name
        return super(ProductInternCatInherit, self).copy(default=default)
    
    @api.onchange('categ_id')
    def field_def_exp(self):
        uom_id = self.env['uom.uom'].search([('name', '=', 'Otro tipo de servicios')])
        if not uom_id:
            msg = "No está creada la unidad de medida Otro tipo de servicios"
            raise ValidationError( _( msg ) )

        company_id = self.env.company
        
        property_account_income_id = self.env['account.account'].search([
            ('name','=','Nacionales'),
            ('company_id.id','=', company_id.id)
        ])
        
        if not property_account_income_id:
            msg = "No está creada cuenta contable: Nacionales"
            raise ValidationError( _( msg ) )
        
        if self.categ_id.id:
            if self.categ_id.name == "Normas":   #3 - Normas
                self.is_enm = True
                self.type = 'service'
                self.uom_id = uom_id.id # 2021 - 	Otro tipo de servicios
                self.property_account_income_id = property_account_income_id.id # 1998 - Nacionales
                #self.cabys_code = '8439900000000'
            else:
                self.is_enm = False
        else:
            self.is_enm = False
    @api.onchange('company_id')
    def field_ed_exp(self):
        if self.edition:
            pass
        else:
            self.edition = 1

    #@api.multi
    def _get_default_code(self):
        """Creates an internal reference for the product template by joining
        some specific fields."""
        if self.default_type:
            defa = self.default_type
            return defa
        else:
            if self.default_code and self.default_code.find("/Enm") >= 0:
                default_c = self.default_code
                return default_c
            else:
                if self.default_code and self.default_code.find("/Cor") >= 0:
                    default_c = self.default_code
                    return default_c
                else:
                    if not self:
                        return False
                    self.ensure_one()
                    standard_categ = self.env.ref('inteco.product_category_1_1',
                                                  raise_if_not_found=False)
                    if not standard_categ or self.categ_id != standard_categ:
                        return False
                    internal_ref = []
                    if self.prefix_id.type == 'I' and self.sector_id:
                        internal_ref.append(self.sector_id.code)
                    if self.short_code:
                        internal_ref.append(self.short_code)
                    parts = list(filter(None, [
                        self.part_one, self.part_two, self.part_three]))
                    if parts:
                        internal_ref.extend(['-' + str(part) for part in parts])
                    # if self.edition:
                    #     internal_ref.extend(['-' + str(self.edition)])
                    if self.year:
                        internal_ref.extend([':' + str(self.year)])
                    internal_ref = [''.join(internal_ref)]
                    if self.prefix_id:
                        internal_ref.insert(0, self.prefix_id.name)
                    return ' '.join(internal_ref)

    @api.depends('product_variant_ids', 'default_code')
    def _compute_default_code(self):
        for product in self:
            product.default_code = product._get_default_code()

    #@api.multi
    def product_history(self, filterby=False):
        """Generates the history of the product. The method return by default
        the entire history. The filterby parameter can be used to return the
        current standard or the new editions."""
        base = self.env['product.template'].search([
            ('id', '=', self.id)], limit=1)
        history = self.env['product.template']
        while base and base not in history:
            history += base
            base = base.new_replaced_by
        if filterby == 'current':
            history = history.filtered(lambda r: not r.new_replaced_by)
        if filterby == 'editions':
            history = history.filtered(lambda r: not r.attribute_value_ids)
        return history

    #@api.multi
    def new_action_product_use_variant_wizard(self):
        view_id = self.env['new.product.use.variant']
        return {
            'type': 'ir.actions.act_window',
            'name': '',
            'res_model': 'new.product.use.variant',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_product_changes.new_view_product_use_variant_form_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def new_action_product_enm_variant_wizard(self):
        view_id = self.env['new.product.enm.variant']
        return {
            'type': 'ir.actions.act_window',
            'name': '',
            'res_model': 'new.product.enm.variant',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_product_changes.new_view_product_Enm_variant_form_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def new_action_product_new_edition_wizard(self):
        view_id = self.env['new.product.new.edition']
        return {
            'type': 'ir.actions.act_window',
            'name': '',
            'res_model': 'new.product.new.edition',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_product_changes.new_view_product_new_edition_form_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    def new_action_product_confirm_wizard(self):
        view_id = self.env['new.product.confirm']
        return {
            'type': 'ir.actions.act_window',
            'name': '',
            'res_model': 'new.product.confirm',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('dfx_product_changes.new_view_product_confirm_form_wizard', False).id,
            'target': 'new',
        }

    #@api.multi
    @api.onchange('mod_type')
    def get_mod_type(self):
        for record in self:
            if record.mod_type != 'mod':
                pass
            else:
                record.default_code = record.default_code + ' ' + 'MOD'
                # record.write({'default_code':record.default_code+'MOD'})

    @api.onchange('confirmation_date')
    def _onchange_confirmation_date(self):
        if self.confirmation_date < self.approval:
            raise ValidationError(
                _("The confirmation date cannot be lower than the approval "
                  "date.")
            )

    @api.onchange('type')
    def dfx_search_domain(self):
        cont = 0
        list = []
        if self.user_has_groups('dfx_product_changes.idl_group'):
            list.append(12)
        if self.user_has_groups('dfx_product_changes.formac_group'):
            list.append(6)
        if self.user_has_groups('dfx_product_changes.event_group'):
            list.append(11)
        if self.user_has_groups('dfx_product_changes.afil_group'):
            list.append(13)
        if self.user_has_groups('dfx_product_changes.serv_evac_group'):
            list.append(4)
        if self.user_has_groups('dfx_product_changes.norm_group'):
            list.append(3)
            list.append(5)
        res = {'domain':
                   {'categ_id': [('id', 'in', list)]}
               }
        return res

    priority = fields.Selection(selection=[
        ('0','Ninguna'),
        ('1','Baja'),
        ('2','Media'),
        ('3', 'Alta')], string='Prioridad')
    state = fields.Selection([
        ('C','Vigente'),
        ('P','Consulta pública'),
        ('V','En desarrollo'),
        ('D','Eliminado'),
        ('R','Sustituido')
    ], string='Estado')
    pages = fields.Integer(string='Páginas')
    previous_code = fields.Char(string='Códigos Anteriores')
    replaced_by = fields.Many2one(comodel_name="product.product", string='Sustituido por')
    standards_ref = fields.Char(string='Referencia en Normas')
    modifier_date = fields.Date(string='Fecha de Modificador')
    # nota: recordar quitar el compute de el campo edition en el modulo inteco en local
    edition = fields.Integer(store=True,help="edition number of the standard."
                             )
    confirmation_date = fields.Date(string='Fecha de Confirmación')
    latest_date = fields.Date(string='Fecha')
    history_norm = fields.Many2many('product.template','product_norm_rel','id', string='Historial de normas')
    norm_processed = fields.Boolean(string='Procesado')
    order_processed = fields.Boolean(string='Orden Procesado')
    product_tp = fields.Many2one(comodel_name="product.template", string='Plantillas')
    product_analytic_account = fields.Many2one(comodel_name="account.analytic.account", string="Cuenta Analítica", tracking=True)


    @api.model
    def check_history_norm(self, limite=25):
        log.info('\n\nINCIANDO PROCESO ')
        self.check_with_dash(limite+4000)
        log.info('\n\nFIN Guiones... \n\n')
        self.check_with_colon(limite+4000)
        log.info('\n\nFIN Dos puntos... \n\n')
        # self.check_all_norm(limite+1000)
        # log.info('\n\nFIN TODO... \n\n')
        log.info('\n\nFIN PROCESO... \n\n')

    @api.model
    def reasign_cascade(self, limite=5):
        products_2proces = self.env['product.template'].search([
            ('norm_processed', '=', True),
            ('order_processed', '=', False)
        ], limit=limite)

        all_products = []
        lista_orden2 = []
        for p in products_2proces:
            if p.product_tp.id not in lista_orden2:
                all_products.append(p)
                lista_orden2.append(p.product_tp.id)

        for product in all_products:

            product_tp_records = self.env['product.template'].search([
                ('product_tp', '=', product.product_tp.id),
                ('order_processed', '=', False)
            ])

            years_to_order = []
            for product_rec in product_tp_records:
                years_to_order.append(self.get_year_from_default(product_rec))

            years_to_order.sort()
            lista_1 = []
            products_dict = {}
            for year in years_to_order:
                for product_rec in product_tp_records:
                    if year == self.get_year_from_default(product_rec):
                        lista_1.append((year, product_rec))
                        products_dict[year] = product_rec
                        break

            cont_1 = 1
            for l in lista_1:
                norm_history_ids = []
                if cont_1 != 1:
                    iteracciones = 0
                    while iteracciones <= len(lista_1)-1:
                        # l[1].history_norm = [4, lista_1[iteracciones][1].id]
                        norm_history_ids.append([4, lista_1[iteracciones][1].id])
                        iteracciones += 1
                        if l[1].id == lista_1[iteracciones][1].id:
                            break
                l[1].order_processed = True
                cont_1 += 1

                if norm_history_ids:
                    l[1].history_norm = norm_history_ids

    def get_year_from_default(self, value):
        d_code = str(value.default_code)
        year_d_code = d_code[len(d_code)-4 : len(d_code)]

        return int(year_d_code)

    @api.model
    def check_with_colon(self, limite=25):
        all_products = self.env['product.template'].search([
            ('categ_id.id', '=', 3),
            ('norm_processed', '=', False),
            ('default_code', '!=', False)
        ], limit=limite)

        for product in all_products:
            name = product.default_code
            num_products = 0
            pos_dash = name.find(":", 0, len(name))
            if pos_dash != -1:
                cont = pos_dash+1
            else:
                continue

            pedacito = name[:cont]
            prod = self.env['product.template'].search([('default_code', 'like', pedacito)])

            if len(prod) > 1:
                products = self.env['product.template'].search([
                    ('default_code', 'like', pedacito),
                    ('norm_processed', '=', False)], order='id asc')

                count_2 = 0
                for producto_updt in products:
                    if count_2 == 0:
                        id = producto_updt
                        producto_updt.norm_processed = True
                    else:
                        producto_updt.history_norm = id
                        producto_updt.norm_processed = True
                    producto_updt.product_tp = id
                    log.info('\nID: ' + str(producto_updt.id))
                    count_2 += 1

    def check_with_dash(self, limite=25):
        all_products = self.env['product.template'].search([
            ('categ_id.id', '=', 3),
            ('norm_processed', '=', False),
            ('default_code', '!=', False)
        ], limit=limite)

        for product in all_products:
            # name = product.name
            name = product.default_code

            num_products = 0

            pos_dash = name.find("-", 0, len(name))
            if pos_dash != -1:
                cont = pos_dash
            else:
                continue

            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('default_code', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('default_code', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True
                        producto_updt.product_tp = id
                        log.info('\nID: ' + str(producto_updt.id))
                        count_2 += 1
                    break

    @api.model
    def check_with_colon2(self, limite=25):
        all_products = self.env['product.template'].search([
            ('categ_id.id', '=', 3),
            ('norm_processed', '=', False),
            ('default_code', '!=', False)
        ], limit=limite)

        for product in all_products:
            # name = product.name
            name = product.default_code

            num_products = 0

            pos_dash = name.find(":", 0, len(name))
            if pos_dash != -1:
                cont = pos_dash+1
            else:
                continue

            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('default_code', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('default_code', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True
                        producto_updt.product_tp = id
                        log.info('\nID: ' + str(producto_updt.id))
                        count_2 += 1
                    break

        def check_with_dash(self, limite=25):
            all_products = self.env['product.template'].search([
                ('categ_id.id', '=', 3),
                ('norm_processed', '=', False),
                ('default_code', '!=', False)
            ], limit=limite)

        for product in all_products:
            # name = product.name
            name = product.default_code

            num_products = 0

            pos_dash = name.find("-", 0, len(name))
            if pos_dash != -1:
                cont = pos_dash
            else:
                continue

            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('default_code', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('default_code', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True
                        producto_updt.product_tp = id
                        log.info('\nID: ' + str(producto_updt.id))
                        count_2 += 1
                    break

    @api.model
    def check_all_norm(self, limite=25):
        all_products = self.env['product.template'].search([
            ('categ_id.id', '=', 3),
            ('norm_processed', '=', False),
            ('default_code', '!=', False)
        ], limit=limite)
        for product in all_products:
            # name = product.name
            name = product.default_code
            cont = 8
            num_products = 0
            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('default_code', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('default_code', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True
                        producto_updt.product_tp = id
                        log.info('\nID: ' + str(producto_updt.id))
                        count_2 += 1
                    break

    @api.model
    def check_with_dash(self, limite=25):
        all_products = self.env['product.template'].search([
            ('categ_id.id', '=', 3),
            ('norm_processed', '=', False),
            ('default_code', '!=', False)
        ], limit=limite)

        for product in all_products:
            # name = product.name
            name = product.default_code

            num_products = 0

            pos_dash = name.find("-", 0, len(name))
            if pos_dash != -1:
                cont = pos_dash
            else:
                continue

            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('default_code', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('default_code', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True
                        producto_updt.product_tp = id
                        log.info('\nID: ' + str(producto_updt.id))
                        count_2 += 1
                    break

        def check_with_dash(self, limite=25):
            all_products = self.env['product.template'].search([
                ('categ_id.id', '=', 3),
                ('norm_processed', '=', False),
                ('default_code', '!=', False)
            ], limit=limite)

        for product in all_products:
            # name = product.name
            name = product.default_code

            num_products = 0

            pos_dash = name.find("-", 0, len(name))
            if pos_dash != -1:
                cont = pos_dash
            else:
                continue

            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('default_code', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('default_code', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True
                        producto_updt.product_tp = id
                        log.info('\nID: ' + str(producto_updt.id))
                        count_2 += 1
                    break

    @api.model
    def clean_history_norm(self, limite = 2000):
        all_products = self.env['product.template'].search([('categ_id.id', '=', 3),
                                                            ('norm_processed', '=', True)], limit=limite)
        for product in all_products:
            product.norm_processed = False
            product.history_norm = False
            product.product_tp = False
            log.info('\nID: ' + str(product.id))

    @api.model
    def clean_history_norm_order_processed(self, limite = 2000):
        all_products = self.env['product.template'].search([('categ_id.id', '=', 3),
                                                            ('order_processed', '=', True)], limit=limite)
        for product in all_products:
            product.order_processed = False
            product.history_norm = False
            log.info('\nID: ' + str(product.id))

    @api.model
    def check_history_norm(self, limite = 5):
        all_products = self.env['product.template'].search([('categ_id.id', '=', 3)], limit=limite)
        for product in all_products:
            name = product.name
            cont = 20
            num_products = 0
            while(cont <= len(name)):

                pedacito = name[:cont]
                prod = self.env['product.template'].search([('name', 'like', pedacito)])
                cont += 1

                if len(prod) > 1:
                    num_products = len(prod)

                if len(prod) == 1 and num_products != 0:
                    new_pedacito = pedacito[:len(pedacito)-1]
                    products = self.env['product.template'].search([
                        ('name', 'like', new_pedacito),
                        ('norm_processed', '=', False)], order='id asc')
                    count_2 = 0
                    for producto_updt in products:
                        if count_2 == 0:
                            id = producto_updt
                            producto_updt.norm_processed = True
                        else:
                            producto_updt.history_norm = id
                            producto_updt.norm_processed = True

                        count_2 += 1
                    break

    @api.model
    def default_get(self, fields_list):
        res = super(ProductInternCatInherit, self).default_get(fields_list)
        exp = self.env['product.category'].search([('name', '=', 'Gastos')])
        res.update({
            'categ_id': ''
        })
        return res

    #@api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self.seller_ids
        if self.env.context.get('force_company'):
            sellers = sellers.filtered(
                lambda s: not s.company_id or s.company_id.id == self.env.context['force_company'])
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom)

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            if float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
                continue
            if seller.product_id and seller.product_id != self:
                continue

            res |= seller
            break
        return res

    def update_price_prod_temp(self):
        for product in records:
            # A
            if product.pages in range(1, 6):
                product.write({'list_price': 7530})
                continue

            # B
            if product.pages in range(6, 11):
                product.write({'list_price': 9540})
                continue

            # C
            if product.pages in range(11, 15):
                product.write({'list_price': 13890})
                continue

            # D
            if product.pages in range(15, 20):
                product.write({'list_price': 17570})
                continue

            # E
            if product.pages in range(20, 30):
                product.write({'list_price': 21750})
                continue

            # F
            if product.pages in range(30, 40):
                product.write({'list_price': 25600})
                continue

            # G
            if product.pages in range(40, 50):
                product.write({'list_price': 30110})
                continue

            # H
            if product.pages in range(50, 70):
                product.write({'list_price': 36300})
                continue

            # I
            if product.pages in range(70, 90):
                product.write({'list_price': 42660})
                continue

            # J
            if product.pages in range(90, 110):
                product.write({'list_price': 50190})
                continue

            # K
            if product.pages in range(110, 130):
                product.write({'list_price': 59060})
                continue

            # L
            if product.pages in range(130, 150):
                product.write({'list_price': 68590})
                continue

            # M
            if product.pages in range(150, 180):
                product.write({'list_price': 80130})
                continue

            # N
            if product.pages in range(180, 210):
                product.write({'list_price': 105060})
                continue

            # Ñ
            if product.pages in range(210, 240):
                product.write({'list_price': 125470})
                continue

            # O
            if product.pages in range(240, 280):
                product.write({'list_price': 119280})
                continue

            # P
            if product.pages in range(280, 320):
                product.write({'list_price': 136450})
                continue

            # Q
            if product.pages in range(320, 360):
                product.write({'list_price': 146410})
                continue

            # R
            if product.pages in range(360, 400):
                product.write({'list_price': 173150})
                continue

            # S
            if product.pages in range(400, 475):
                product.write({'list_price': 191240})
                continue

            # T
            if product.pages > 475:
                product.write({'list_price': 209710})
                continue

    # #@api.multi
    # @api.depends('approval')
    # def _compute_year(self):
    #     """Updates the year depending of the approval date."""
    #     for product in self:
    #         if product.approval:
    #             val = fields.Date.from_string(product.approval).strftime('%Y')
    #             product.year = val.replace(',', "")

    # #@api.multi
    # @api.depends('default_code')
    # def _compute_edition(self):
    #     """Compute the edition number depending on the number of templates
    #     and their year."""
    #     for product in self:
    #         domain = [
    #             ('prefix_id', '=', product.prefix_id.id),
    #             ('short_code', '=', product.short_code),
    #         ]
    #         if product.part_one:
    #             domain += [
    #                 ('part_one', '=', product.part_one),
    #             ]
    #         if product.part_two:
    #             domain += [
    #                 ('part_two', '=', product.part_two),
    #             ]
    #         if product.part_three:
    #             domain += [
    #                 ('part_three', '=', product.part_three),
    #             ]
    #         if product.prefix_id.type == 'I' and product.sector_id:
    #             domain += [
    #                 ('sector_id', '=', product.sector_id.id),
    #             ]
    #         templates = self.env['product.template'].search(
    #             domain).sorted('year').mapped('default_code')
    #
    #         if product.default_code in templates:
    #             product.edition = templates.index(product.default_code) + 1

class ProductVariantInherit(models.Model):
    _inherit = "product.product"
    _description = 'valor por defecto en un campo'

    mod_type = fields.Selection([
        ('mod', 'Modificada'),
        ('partial', 'Parcial'),
        ('iden', 'Idéntica'),
        ('None_type', 'N/A')
    ], string='Tipo de modificación')
    course_duration = fields.Integer(string='Duración del Curso')
    course_req = fields.Char(string='Requisitos del Curso')

    # year = fields.Char(compute='_compute_year', string='Año', store=True,
    #     help="year of the standard.")

    lst_price = fields.Monetary(string='Precio de venta')
    key_words = fields.Many2many(comodel_name="prod.key.words", string='Palabras Clave')

    @api.model
    def create(self, values):
        # Herencia para que se guarde la categoria del producto y el coste
        if values.get('product_tmpl_id', False):
            tmpl_id = values.get('product_tmpl_id', False)
            product_tmpl_id = self.env['product.template'].browse(tmpl_id)
            values.update({'categ_id': product_tmpl_id.categ_id.id})

            if product_tmpl_id.list_price != 0:
                values.update({'lst_price': product_tmpl_id.list_price})

        return super(ProductVariantInherit, self).create(values)

    def update_default_code(self):
        products_toupd = self.env['product.product'].search([
            ('default_code', '=',None),
            ('categ_id', '=', None),
            ('year', '!=', None)
        ])
        for rec in products_toupd:
            if rec.product_tmpl_id.categ_id.id == 3:
                rec.categ_id = rec.product_tmpl_id.categ_id
                rec._compute_default_code()
                log.info('\nID: ' + str(rec.id) + '  REFERENCIA INT: ' + str(rec.default_code) + ' NAME: ' + str(rec.name))

    @api.onchange('type')
    def dfx_search_domain(self):
        cont = 0
        list = []
        if self.user_has_groups('dfx_product_changes.idl_group'):
            list.append(12)
        if self.user_has_groups('dfx_product_changes.formac_group'):
            list.append(6)
        if self.user_has_groups('dfx_product_changes.event_group'):
            list.append(11)
        if self.user_has_groups('dfx_product_changes.afil_group'):
            list.append(13)
        if self.user_has_groups('dfx_product_changes.serv_evac_group'):
            list.append(4)
        if self.user_has_groups('dfx_product_changes.norm_group'):
            list.append(3)
            list.append(5)
        res = {'domain':
                   {'categ_id': [('id', '=', list)]}
               }
        return res

    #@api.multi
    @api.depends('confirmation_date', 'modifier_date', 'approval')
    def _compute_latest_date(self):
        for product in self:
            if product.approval:
                product.latest_date = str(product.approval)
            else:
                if product.confirmation_date:
                    product.latest_date = str(product.confirmation_date)
                else:
                    if product.modifier_date:
                        product.latest_date = str(product.modifier_date)
                    else:
                        pass

    #@api.multi
    @api.onchange('mod_type')
    def get_mod_type(self):
        for record in self:
            if record.mod_type != 'mod':
                pass
            else:
                record.default_code = record.default_code + ' ' + 'MOD'
                # record.write({'default_code':record.default_code+'MOD'})

    # @api.model
    # def create(self, vals):
    #     variant_product = super(Sale_Norm_Catalog_Inherit, self).create(vals)
    #     for record in self:
    #         if record.year:
    #             record.default_code = record.default_code+':'+record.year
    #     return variant_product

    #@api.multi
    def _get_default_code(self):
        """Creates an internal reference for the product template by joining
        some specific fields."""
        if not self:
            return False
        self.ensure_one()
        standard_categ = self.env.ref('inteco.product_category_1_1',
                                      raise_if_not_found=False)
        if not standard_categ or self.categ_id != standard_categ:
            return False
        internal_ref = []
        if self.prefix_id.type == 'I' and self.sector_id:
            internal_ref.append(self.sector_id.code)
        if self.short_code:
            internal_ref.append(self.short_code)
        parts = list(filter(None, [
            self.part_one, self.part_two, self.part_three]))
        if parts:
            internal_ref.extend(['-' + str(part) for part in parts])
        if self.year:
            internal_ref.extend([':' + str(self.year)])
        internal_ref = [''.join(internal_ref)]
        if self.prefix_id:
            internal_ref.insert(0, self.prefix_id.name)
        return ' '.join(internal_ref)


    # #@api.multi
    # def _get_default_code(self):
    #     """Creates an internal reference for the product template by joining
    #     some specific fields."""
    #     if not self:
    #         return False
    #     self.ensure_one()
    #     standard_categ = self.env.ref('inteco.product_category_1_1',
    #                                   raise_if_not_found=False)
    #     if not standard_categ or self.categ_id != standard_categ:
    #         return False
    #     attr_modifier = self.env.ref(
    #         'inteco.modifier_attribute', raise_if_not_found=False)
    #     attr_modifier_num = self.env.ref(
    #         'inteco.modifier_number_attribute', raise_if_not_found=False)
    #     attr_modifier_year = self.env.ref(
    #         'inteco.modifier_year_attribute', raise_if_not_found=False)
    #     val_modifier = (
    #         self.attribute_value_ids.filtered(
    #             lambda x: x.attribute_id == attr_modifier)
    #         if attr_modifier else False)
    #     val_modifier_num = (
    #         self.attribute_value_ids.filtered(
    #             lambda x: x.attribute_id == attr_modifier_num)
    #         if attr_modifier_num else False)
    #     val_modifier_year = (
    #         self.attribute_value_ids.filtered(
    #             lambda x: x.attribute_id == attr_modifier_year)
    #         if attr_modifier_year else False)
    #     internal_ref = []
    #     if self.prefix_id.type == 'I' and self.sector_id:
    #         internal_ref.append(self.sector_id.code)
    #     if self.short_code:
    #         internal_ref.append(self.short_code)
    #     parts = list(filter(None, [
    #         self.part_one, self.part_two, self.part_three]))
    #     if parts:
    #         internal_ref.extend(['-' + str(part) for part in parts])
    #     if self.year:
    #         internal_ref.extend([':' + str(self.year)])
    #     internal_ref = [''.join(internal_ref)]
    #     if self.prefix_id:
    #         internal_ref.insert(0, self.prefix_id.name)
    #     attrib = ''
    #     if all([val_modifier, val_modifier_num, val_modifier_year]):
    #         attrib = '/%s %s:%s' % (
    #             val_modifier.name, val_modifier_num.name,
    #             val_modifier_year.name)
    #     default_code = self._get_default_code()
    #     return (default_code + attrib) if default_code else False

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        for product in self:
            product.default_code = product._get_default_code()

    # @api.onchange('type')
    # def field_def_exp(self):
    #     exp = self.env['product.category'].search([('name','=','Gastos')])
    #     self.categ_id = exp.id

    categ_id = fields.Many2one(comodel_name="product.category", required=False)
    # price_vali = fields.Boolean(string='Precio de Venta?')

    #@api.multi
    @api.depends('approval')
    def _compute_year(self):
        """Updates the year depending of the approval date."""
        for product in self:
            if product.approval:
                val = fields.Date.from_string(product.approval).strftime('%Y')
                product.year = val.replace(',',"")

    def update_price_prod(self):
        for product in self:
            if product.lst_price:
                # A
                if product.pages in range(1, 5):
                    product.write({'price': 6550})
                    continue

                # B
                if product.pages in range(6, 10):
                    product.write({'price': 8290})
                    continue

                # C
                if product.pages in range(11, 15):
                    product.write({'price': 12070})
                    continue

                # D
                if product.pages in range(16, 20):
                    product.write({'price': 15270})
                    continue

                # E
                if product.pages in range(21, 30):
                    product.write({'price': 18910})
                    continue

                # F
                if product.pages in range(31, 40):
                    product.write({'price': 22260})
                    continue

                # G
                if product.pages in range(41, 50):
                    product.write({'price': 26190})
                    continue

                # H
                if product.pages in range(51, 70):
                    product.write({'price': 31570})
                    continue

                # I
                if product.pages in range(71, 90):
                    product.write({'price': 37100})
                    continue

                # J
                if product.pages in range(91, 110):
                    product.write({'price': 43640})
                    continue

                # K
                if product.pages in range(111, 130):
                    product.write({'price': 51350})
                    continue

                # L
                if product.pages in range(131, 150):
                    product.write({'price': 59640})
                    continue

                # M
                if product.pages in range(151, 180):
                    product.write({'price': 69680})
                    continue

                # N
                if product.pages in range(181, 210):
                    product.write({'price': 91360})
                    continue

                # Ñ
                if product.pages in range(211, 240):
                    product.write({'price': 109110})
                    continue

                # O
                if product.pages in range(241, 280):
                    product.write({'price': 103720})
                    continue

                # P
                if product.pages in range(281, 320):
                    product.write({'price': 118650})
                    continue

                # Q
                if product.pages in range(321, 360):
                    product.write({'price': 127310})
                    continue

                # R
                if product.pages in range(361, 400):
                    product.write({'price': 150570})
                    continue

                # S
                if product.pages in range(401, 475):
                    product.write({'price': 166290})
                    continue

                # T
                if product.pages > 475:
                    product.write({'price': 182350})
                    continue

            else:
                tem_id = self.env['product.template'].search([('id', '=', product.product_tmpl_id.id)])
                if tem_id:
                    tem_id.list_price = product.lst_price

    # #@api.multi
    # @api.depends('default_code')
    # def _compute_edition(self):
    #     """Compute the edition number depending on the number of templates
    #     and their year."""
    #     for product in self:
    #         domain = [
    #             ('prefix_id', '=', product.prefix_id.id),
    #             ('short_code', '=', product.short_code),
    #         ]
    #         if product.part_one:
    #             domain += [
    #                 ('part_one', '=', product.part_one),
    #             ]
    #         if product.part_two:
    #             domain += [
    #                 ('part_two', '=', product.part_two),
    #             ]
    #         if product.part_three:
    #             domain += [
    #                 ('part_three', '=', product.part_three),
    #             ]
    #         if product.prefix_id.type == 'I' and product.sector_id:
    #             domain += [
    #                 ('sector_id', '=', product.sector_id.id),
    #             ]
    #         templates = self.env['product.template'].search(
    #             domain).sorted('year').mapped('default_code')
    #
    #         if product.default_code in templates:
    #             product.edition = templates.index(product.default_code) + 1



class ProductCatInherit(models.Model):
    _inherit = "product.category"
    _description = 'añadir validación para productos'

    valid_product = fields.Boolean(string="Aparecer en Productos?")
    group_valid = fields.Many2one(comodel_name="res.groups", string="Permiso Asociado", required=False)
    analytic_account_def = fields.Many2one("account.analytic.account", string="Cuenta Analitica", tracking=True)

class Sale_New_Norm_Inherit(models.TransientModel):
    _inherit = "product.new.edition"
    _description = 'añadir campos a la vista Nueva Edición'

    mod_type = fields.Selection([
        ('mod', 'Modificada'),
        ('partial', 'Parcial'),
        ('iden', 'Idéntica'),
        ('None_type', 'N/A')
    ], string='Tipo de modificación')
    lst_price = fields.Integer(string="Precio")
    edition = fields.Char(string="Edición")

class SaleOrderPreviChanges(models.Model):
    _inherit = 'sale.order'

    def order_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
            # If last added category induced a pagebreak, this one will be on a new page
            if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                report_pages.append([])
            # Append category to current report page
            report_pages[-1].append({
                'name': category and category.name or _('Uncategorized'),
                'subtotal': category and category.subtotal,
                'pagebreak': category and category.pagebreak,
                'lines': list(lines)
            })

        return report_pages
