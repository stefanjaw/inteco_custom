# -*- coding: utf-8 -*-

from odoo.addons.website_event_sale.models.sale_order import SaleOrderLine, SaleOrder

from odoo import api, models, fields, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderEspecialInherit(SaleOrder):
    _inherit = "sale.order"
    
    # Esta herencia es para sobrescribir  el metodo _website_product_id_change del modelo SaleOrder
    
    def _website_product_id_change(self, order_id, product_id, qty=0):
        order = self.env['sale.order'].sudo().browse(order_id)
        if self._context.get('pricelist') != order.pricelist_id.id:
            self = self.with_context(pricelist=order.pricelist_id.id)
    
        values = super(SaleOrderInherit, self)._website_product_id_change(order_id, product_id, qty=qty)
        event_ticket_id = None
        if self.env.context.get("event_ticket_id"):
            event_ticket_id = self.env.context.get("event_ticket_id")
        else:
            product = self.env['product.product'].browse(product_id)
            if product.event_ticket_ids:
                event_ticket_id = product.event_ticket_ids[0].id
    
        if event_ticket_id:
            ticket = self.env['event.event.ticket'].browse(event_ticket_id)
            if product_id != ticket.product_id.id:
                raise UserError(_("The ticket doesn't match with this product."))
        
            values['product_id'] = ticket.product_id.id
            values['event_id'] = ticket.event_id.id
            values['event_ticket_id'] = ticket.id
            if order.pricelist_id.discount_policy == 'without_discount':
                values['price_unit'] = ticket.price
            else:
                values['price_unit'] = ticket.price_reduce
            #values['name'] = ticket._get_ticket_multiline_description() TODO Eliminado para que no cambie la descripcion del SO
    
        # avoid writing related values that end up locking the product record
        values.pop('event_ok', None)
    
        return values


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"
    
    def _inteco_cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        OrderLine = self.env['sale.order.line']
        
        try:
            if add_qty:
                add_qty = float(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = float(set_qty)
        except ValueError:
            set_qty = 0
        
        if line_id:
            line = OrderLine.browse(line_id)
            ticket = line.event_ticket_id
            old_qty = int(line.product_uom_qty)
            if ticket.id:
                self = self.with_context(event_ticket_id=ticket.id, fixed_price=1)
        else:
            line = None
            ticket = self.env['event.event.ticket'].search([('product_id', '=', product_id)], limit=1)
            old_qty = 0
        new_qty = set_qty if set_qty else (add_qty or 0 + old_qty)
        
        # case: buying tickets for a sold out ticket
        values = {}
        if ticket and ticket.seats_limited and ticket.seats_available <= 0:
            values['warning'] = _('Sorry, The %(ticket)s tickets for the %(event)s event are sold out.') % {
                'ticket': ticket.name,
                'event': ticket.event_id.name}
            new_qty, set_qty, add_qty = 0, 0, -old_qty
        # case: buying tickets, too much attendees
        elif ticket and ticket.seats_limited and new_qty > ticket.seats_available:
            values['warning'] = _('Sorry, only %(remaining_seats)d seats are still available for the %(ticket)s ticket for the %(event)s event.') % {
                'remaining_seats': ticket.seats_available,
                'ticket': ticket.name,
                'event': ticket.event_id.name}
            new_qty, set_qty, add_qty = ticket.seats_available, ticket.seats_available, 0
        values.update(super(SaleOrderInherit, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs))
        
        # removing attendees
        if ticket and new_qty < old_qty:
            attendees = self.env['event.registration'].search([
                ('state', '!=', 'cancel'),
                ('sale_order_id', 'in', self.ids),  # To avoid break on multi record set
                ('event_ticket_id', '=', ticket.id),
            ], offset=new_qty, limit=(old_qty - new_qty), order='create_date asc')
            attendees.action_cancel()
        # adding attendees
        elif ticket and new_qty > old_qty:
            #Esta parte se agrega de nuevo para usarse en este modulo
            line = OrderLine.browse(values['line_id'])
            line._update_registrations(confirm=False, cancel_to_draft=True, registration_data=kwargs.get('registration_data', []))
            # add in return values the registrations, to display them on website (or not)
            values['attendee_ids'] = self.env['event.registration'].search([('sale_order_line_id', '=', line.id), ('state', '!=', 'cancel')]).ids
        return values


    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
        # change lang to get correct name of attributes/values
        product_with_context = self.env['product.product'].with_context(product_context)
        product = product_with_context.browse(int(product_id))
    
        try:
            if add_qty:
                add_qty = float(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = float(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]
    
        # Create line if no line with product_id can be located
        if not order_line:
            if not product:
                raise UserError(_("The given product does not exist therefore it cannot be added to cart."))
        
            no_variant_attribute_values = kwargs.get('no_variant_attribute_values') or []
            received_no_variant_values = product.env['product.template.attribute.value'].browse([int(ptav['value']) for ptav in no_variant_attribute_values])
            received_combination = product.product_template_attribute_value_ids | received_no_variant_values
            product_template = product.product_tmpl_id
        
            # handle all cases where incorrect or incomplete data are received
            combination = product_template._get_closest_possible_combination(received_combination)
        
            # get or create (if dynamic) the correct variant
            product = product_template._create_product_variant(combination)
        
            if not product:
                raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))
        
            product_id = product.id
        
            values = self._website_product_id_change(self.id, product_id, qty=1)
        
            # add no_variant attributes that were not received
            for ptav in combination.filtered(lambda ptav: ptav.attribute_id.create_variant == 'no_variant' and ptav not in received_no_variant_values):
                no_variant_attribute_values.append({
                    'value': ptav.id,
                })
        
            # save no_variant attributes values
            if no_variant_attribute_values:
                values['product_no_variant_attribute_value_ids'] = [
                    (6, 0, [int(attribute['value']) for attribute in no_variant_attribute_values])
                ]
        
            # add is_custom attribute values that were not received
            custom_values = kwargs.get('product_custom_attribute_values') or []
            received_custom_values = product.env['product.template.attribute.value'].browse([int(ptav['custom_product_template_attribute_value_id']) for ptav in custom_values])
        
            for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
                custom_values.append({
                    'custom_product_template_attribute_value_id': ptav.id,
                    'custom_value': '',
                })
        
            # save is_custom attributes values
            if custom_values:
                values['product_custom_attribute_value_ids'] = [(0, 0, {
                    'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value']
                }) for custom_value in custom_values]
        
            # create the line
            order_line = SaleOrderLineSudo.create(values)
        
            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1
    
        # compute new quantity
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)
    
        # Remove zero of negative lines
        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                # update description of the parent
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
        else:
            # update line
            no_variant_attributes_price_extra = [ptav.price_extra for ptav in order_line.product_no_variant_attribute_value_ids]
            values = self.with_context(no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra))._website_product_id_change(self.id, product_id, qty=quantity)
            if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
                order = self.sudo().browse(self.id)
                product_context.update({
                    'partner': order.partner_id,
                    'quantity': quantity,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                })
                product_with_context = self.env['product.product'].with_context(product_context).with_company(order.company_id.id)
                product = product_with_context.browse(product_id)
                values['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                    order_line._get_display_price(product),
                    order_line.product_id.taxes_id,
                    order_line.tax_id,
                    self.company_id
                )
        
            order_line.write(values)
        
            # link a product to the sales order
            if kwargs.get('linked_line_id'):
                linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
                order_line.write({
                    'linked_line_id': linked_line.id,
                })
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
            # Generate the description with everything. This is done after
            # creating because the following related fields have to be set:
            # - product_no_variant_attribute_value_ids
            # - product_custom_attribute_value_ids
            # - linked_line_id
            #order_line.name = order_line.get_sale_order_line_multiline_description_sale(product) TODO Eliminado para que no cambie la descripcion
    
        option_lines = self.order_line.filtered(lambda l: l.linked_line_id.id == order_line.id)
    
        return {'line_id': order_line.id, 'quantity': quantity, 'option_ids': list(set(option_lines.ids))}


class SaleOrderLineInherit(SaleOrderLine):
    _inherit = "sale.order.line"
    
    @api.depends('product_id.display_name', 'event_ticket_id.display_name')
    def _compute_name_short(self):
        """ Compute a short name for this sale order line, to be used on the website where we don't have much space.
            To keep it short, instead of using the first line of the description, we take the product name without the internal reference.
        """
        for record in self:
            record.name_short = record.product_id.with_context(display_default_code=False).display_name
