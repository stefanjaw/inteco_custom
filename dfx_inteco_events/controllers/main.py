from odoo import http, api, models, _
from odoo.addons.website_event_sale.controllers.main import WebsiteEventSaleController  # Import the class
from odoo.addons.website_event.controllers.main import WebsiteEventController  # Import the class
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
import werkzeug

class DFXWebsiteEventController(WebsiteEventSaleController):

    def _process_registration_details(self, details):
        ''' Process data posted from the attendee details form. '''
        registrations = {}
        global_values = {}
        for key, value in details.items():
            if key != 'route':
                counter, field_name = key.split('-', 1)
                if counter == '0':
                    global_values[field_name] = value
                else:
                    registrations.setdefault(counter, dict())[field_name] = value
        for key, value in global_values.items():
            for registration in registrations.values():
                registration[key] = value
        return list(registrations.values())

    @http.route()
    def registration_confirm(self, event, **post):
        """
        Este metodo reescribe registration_confirm para utilizar _inteco_cart_update
        """
        order = request.website.sale_get_order(force_create=1)
        attendee_ids = set()

        registrations = self._process_registration_details(post)
        for registration in registrations:
            if registration.get('ticket_id'):
                ticket = request.env['event.event.ticket'].sudo().browse(int(registration['ticket_id']))
                cart_values = order.with_context(event_ticket_id=ticket.id, fixed_price=True)._inteco_cart_update(
                    product_id=ticket.product_id.id,
                    add_qty=1,
                    registration_data=[registration])
                attendee_ids |= set(cart_values.get('attendee_ids', []))

        # free tickets -> order with amount = 0: auto-confirm, no checkout
        if not order.amount_total:
            order.action_confirm()  # tde notsure: email sending ?
            attendees = request.env['event.registration'].browse(list(attendee_ids)).sudo()
            # clean context and session, then redirect to the confirmation page
            request.website.sale_reset()
            urls = event._get_event_resource_urls()
            return request.render("website_event.registration_complete", {
                'attendees': attendees,
                'event': event,
                'google_url': urls.get('google_url'),
                'iCal_url': urls.get('iCal_url')
            })

        attendees = request.env['event.registration'].browse(list(attendee_ids)).sudo()

        event_id = order.order_line.event_id.id
        event_ticket_id = order.order_line.event_ticket_id.id
        product_id = order.order_line.product_id.id
        product_uom = order.order_line.product_uom.id
        price_unit = order.order_line.price_unit
        line_delete = order.order_line[0]
        line_delete.event_id = None
        line_delete.event_ticket_id = None

        cont = 1
        for attende in attendees:
            if attende.sale_order_line_id.order_id.user_id:
                pass
            else:
                user_event_id = request.env['event.comertial'].search([])
                attende.sale_order_line_id.order_id.user_id = user_event_id.comertial_name.id
            values = {
                'order_id': order.id,
                'product_id': product_id,
                'product_uom_qty': 1,
                'name': attende.event_id.name+'/'+attende.name+'/'+str(attende.att_ident),
                'product_uom': product_uom,
                'event_id': event_id,
                'event_ticket_id': event_ticket_id,
                'price_unit': price_unit
            }
            if cont == 1:
                line_delete.write(values)
                cont+=1
            else:
                line_id = request.env['sale.order.line'].create(values)
                attende.sale_order_line_id = line_id



        return request.redirect("/shop/checkout")


class DFXWebsiteEventControllerInherit(WebsiteEventController):
    
    @http.route(['/event/registration/new_attendees'], type='http', auth="public",  methods=['GET', 'POST'], website=True)
    def registration_new(self,event=None, route=None, **post):
    
        public_user = int(request.env['ir.config_parameter'].sudo().get_param('public_user', 4))

        if request.env.user and request.env.user.id and request.env.user.id != public_user:
            pass
        else:
            if event:
                envent_id = int(event)
                event = request.env['event.event'].sudo().search([('id', '=', envent_id)])
                event_slug = slug(event)
            return request.redirect("/web/login?redirect=/event/" + event_slug)
        
        if not event:
            #Si se hace F5 la pagina se carga en blanco, por lo que redirigimos a eventos
            return request.redirect("/event")
        
        if event:
            envent_id = int(event)
            event = request.env['event.event'].sudo().search([('id', '=', envent_id)])
        
        if not event.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
    
        tickets = self._process_tickets_form(event, post)
        availability_check = True
        if event.seats_limited:
            ordered_seats = 0
            for ticket in tickets:
                ordered_seats += ticket['quantity']
            if event.seats_available < ordered_seats:
                availability_check = False
        if not tickets:
            return False
        data =  {'tickets': tickets, 'event': event, 'availability_check': availability_check, 'route': slug(event)}
    
        return request.env['ir.ui.view']._render_template(
            "dfx_inteco_events.dfx_registration_attendee_template",
            data
        )
        
