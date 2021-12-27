# -*- coding: utf-8 -*-
from odoo import models, fields, api, http, _
from datetime import datetime
from pytz import timezone
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from itertools import groupby


class ChangeSaleOrderConditions(models.Model):
    _inherit = 'sale.order'

    condition = fields.Html(string="Condición")
    process_type = fields.Many2one(comodel_name="process.type", string='Tipos de Procesos')
    sale_contacts = fields.Many2one(comodel_name="res.users", string="Nombre del Firmante", required=False)
    sales_contacts = fields.Many2one(comodel_name="res.partner", string="Nombre del Firmante", required=False)
    signature_id = fields.Char(string='Cédula del Firmante', readonly=True)
    signature_pos = fields.Char(string='Puesto del Firmante', readonly=True)
    sale_record = fields.Char(string='Registro', compute='get_rec_ver')
    sale_version = fields.Char(string='Número de versión', compute='get_rec_ver')
    english_type = fields.Boolean(string='Plantilla en Ingles?', compute="get_engtype")
    eco_cond = fields.Boolean(string='Condición económica diferenciada')
    res_eco_cond = fields.Char(string='Condición económica diferenciada', compute="get_eco_cond")
    desc_res_eco = fields.Char(string='--')
    required_fi = fields.Boolean(string='Condición campos requeridos', compute='calc_group')
    serv_required_fi = fields.Boolean(string='Condición campos requeridos(servicios)', compute='serv_calc_group')

    @api.onchange('sale_order_template_id')
    def calc_group(self):
        # if self.user_has_groups('dfx_product_changes.norm_group') or \
        #         self.user_has_groups('dfx_product_changes.serv_evac_group') or \
        #         self.user_has_groups('dfx_product_changes.afil_group') or \
        #         self.user_has_groups('dfx_product_changes.event_group') or \
        #         self.user_has_groups('dfx_product_changes.formac_group') or \
        #         self.user_has_groups('dfx_product_changes.idl_group'):
        for record in self:
            if record.sale_order_template_id.categ_template == 'evac_ser':
                record.required_fi = True
            else:
                record.required_fi = False

    @api.onchange('sale_order_template_id')
    def serv_calc_group(self):
        for record in self:
            # if record.user_has_groups('dfx_product_changes.serv_evac_group'):
            if record.sale_order_template_id.categ_template == 'evac_ser':
                record.serv_required_fi = True
            else:
                record.serv_required_fi = False

    def get_engtype(self):
        eng = self.env['sale.order.template'].search([('id', '=', self.sale_order_template_id.id)])
        if eng.sale_rec and eng.sale_ver:
            self.write({
                'sale_record': eng.sale_rec or None,
            })
            self.write({
                'sale_version': eng.sale_ver or None,
            })

        if eng.en_temp == True:
            self.english_type = True
        else:
            self.english_type = False

    @api.onchange('eco_cond')
    def get_eco_cond(self):
        for record in self:
            if record.eco_cond == True:
                record.res_eco_cond = 'Si'
            else:
                record.res_eco_cond = 'No'

    @api.onchange('sale_order_template_id','style')
    def get_rec_ver(self):
        for rec in self:
            tep = self.env['sale.order.template'].search([('id', '=', rec.sale_order_template_id.id)])
            if len(tep) > 0 and tep.sale_rec and tep.sale_ver:
                rec.sale_record = tep.sale_rec or None
                rec.sale_version = tep.sale_ver or None
            else:
                rec.sale_record = None
                rec.sale_version = None


    def button_val(self):
        import calendar

        eng = self.env['sale.order.template'].search([('id', '=', self.sale_order_template_id.id)])
        for record in self:
            emp_spc = ' '
            nom = ''
            nif = ''
            addr = ''
            if record.partner_id:
                if record.partner_id.contact_name:
                    if record.partner_id.second_last_name:
                        nom = (record.partner_id.contact_name + ' ' + record.partner_id.contact_last_name + ' ' + record.partner_id.second_last_name)
                    else:
                        nom = (record.partner_id.contact_name + ' ' + record.partner_id.contact_last_name)
                else:
                    nom = str(record.partner_id.name)
                nif = (record.partner_id.vat or ' ')
                addr =(record.partner_id.street or ' ')
                user_province = str(record.env.user.city or ' ')

            user_id = str(record.signature_id or '')
            pur_num = str(record.name)
            pos = str(record.signature_pos or '')
            user_nom = str(record.sales_contacts.name or '')
            # date_today = datetime.now()
            # date_day = date_today.strftime("%d")
            # date_month = date_today.strftime("%m")
            # date_month_name = calendar.month_name[int(date_month)]
            # date_year = date_today.strftime("%Y")

            # fmt = "%I:%M %p"
            # now_utc = datetime.now(timezone('UTC'))
            # now_pac = now_utc.astimezone(timezone(record.env.user.tz))
            # date_time = now_pac.strftime(fmt)

            # name_year = {
            #     'January': 'Enero',
            #     'February': 'Febrero',
            #     'March': 'Marzo',
            #     'April': 'Abril',
            #     'May': 'Mayo',
            #     'June': 'Junio',
            #     'July': 'Julio',
            #     'August': 'Agosto',
            #     'September': 'Septiembre',
            #     'October': 'Octubre',
            #     'November': 'Noviembre',
            #     'December': 'Diciembre',
            #     'january': 'Enero',
            #     'february': 'Febrero',
            #     'march': 'Marzo',
            #     'april': 'Abril',
            #     'may': 'Mayo',
            #     'june': 'Junio',
            #     'july': 'Julio',
            #     'august': 'Agosto',
            #     'september': 'Septiembre',
            #     'october': 'Octubre',
            #     'november': 'Noviembre',
            #     'december': 'Diciembre',
            #     'enero': 'January',
            #     'febrero': 'February',
            #     'marzo': 'March',
            #     'abril': 'April',
            #     'mayo': 'May',
            #     'junio': 'June',
            #     'julio': 'July',
            #     'agosto': 'August',
            #     'septiembre': 'September',
            #     'octubre': 'October',
            #     'noviembre': 'November',
            #     'diciembre': 'December',
            #     'Enero': 'January',
            #     'Febrero': 'February',
            #     'Marzo': 'March',
            #     'Abril': 'April',
            #     'Mayo': 'May',
            #     'Junio': 'June',
            #     'Julio': 'July',
            #     'Agosto': 'August',
            #     'Septiembre': 'September',
            #     'Octubre': 'October',
            #     'Noviembre': 'November',
            #     'Diciembre': 'December'
            # }

            nom_firm = '(Nombre Representante legal, del cliente)'
            en_nom_firm = '(Name of the legal representative of the client)'
            nom_firm_ra = '_______________________________________'
            nom_dic = '(Nombre Director Ejecutivo de INTECO)'
            en_nom_dic = '(Name of INTECO Executive Director)'
            nom_dic_ra = '_______________________________________'

            phrase = 'Por la presente, el cliente,'+' '+nom+' '+'con cédula'+' '+nif+' '+'y domicilio social'+' '+addr+' ' \
                                                                                                                       ',representada legalmente por'+' '+ user_nom + ',número de identificación personal'+' '+user_id+ \
                     ', en su condición de'+' '+pos+ ',  acepta en todos sus términos la oferta número'+' '+pur_num+', ' \
                                                                                                                    'verifica la exactitud de sus datos y declara conocer y obligarse a cumplir lo especificado en ' \
                                                                                                                    'la sección 5 de este documento y en el Anexo 1.' \
                     + '<br/>' \
                     + '<br/>' \
                     +' '+'Leída la presente oferta, las partes la encuentran conforme en todos sus términos y la firman en ' \
                          'prueba de aceptación, en el lugar y fecha expresados en el mismo.' \
                          ' ' \
                          'Firmado en'+' '+'......................'+' '+','+'a las'+' '+'...............'+' '+'horas del' \
                     +' '+'.............'+' '+'de'+' '+'................'+' '+ 'de' +' '+'.................'+'.'+'<br/>' \
                     +'<br/>' \
                     +'&emsp;'+'&emsp;'+'&emsp;'+'&emsp;'+nom_firm_ra+'&emsp;'+'&emsp;'+'&emsp;'+nom_dic_ra+'<br/>' \
                     +'&emsp;'+'&emsp;'+'&emsp;'+'&emsp;'+nom_dic+'&emsp;'+'&emsp;'+'&emsp;'+'&emsp;'+'&emsp;'+nom_firm

            phrase_cond = '<br/>' \
                          +'<br/>' \
                          + '<br/>' \
                          +'Anexo 1' \
                          + '<br/>' \
                          +'Condiciones legales' \
                          + '<br/>' \
                          + '<br/>' \
                          + '1.	DERECHOS DE AUTOR. Todo el trabajo realizado por los auditores culminará en la certificación ' \
                            'respectiva que se otorgue al cliente, en cuyo caso los derechos de autor corresponderán a las personas ' \
                            'físicas que participen del proceso y los derechos patrimoniales a INTECO. La información que entregue el ' \
                            'cliente, no formará parte de esos derechos.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.	CONFIDENCIALIDAD Y SECRETO PROFESIONAL. Las cláusulas y estipulaciones de esta oferta y del acuerdo ' \
                            'se inspiran en los más depurados principios de lealtad, equidad y buena fe, que recíprocamente guardan y ' \
                            'guardarán las partes y, en consecuencia, dichas cláusulas y estipulaciones serán de observancia obligatoria ' \
                            'para los efectos de su interpretación y aplicación. Cada parte se obliga con la otra y por todo el tiempo ' \
                            'que dure este contrato y más allá del mismo una vez que haya finalizado, a lo siguiente: ' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.1.	No comunicar, divulgar, suministrar o de cualquier forma poner a disposición de persona alguna, ' \
                            'ya sea de forma directa o indirecta Información de recibida por las partes. Se exceptúa de lo anterior:' \
                          + '<br/>' \
                          + 'i.	Si dicha divulgación es requerida por aplicación de disposiciones legales o por orden judicial u ' \
                            'otra orden coactiva similar' \
                          + '<br/>' \
                          + 'ii.	Cuando las partes expresamente lo autoricen por escrito. ' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.2.	No hacer manifestaciones públicas sobre el contenido este Contrato, sin el consentimiento ' \
                            'previo y por escrito de la otra parte.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.3.	Se reconoce que cada parte tendrá derecho a que se ordene el cumplimiento específico en caso' \
                            ' de un incumplimiento de este acuerdo de confidencialidad, además de cualquier otro derecho o recurso' \
                            ' de conformidad con la ley, sea un derecho a una compensación por daños o perjuicios.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '3.	DENUNCIAS POR DERECHOS DEL CONSUMIDOR, CIVILES, PENALES Y/O ADMINISTRATIVOS. INTECO no tendrá ' \
                            'ninguna responsabilidad final por los productos y/o servicios que el cliente llegue a comercializar, ' \
                            'ya sean derechos del consumidor, civiles, penales y/o administrativos, temas que deberá enfrentar el ' \
                            'cliente por sí solo. ' \
                          + '<br/>' \
                          + '<br/>' \
                          + '4.	RESPONSABILIDADES SOCIALES Y LABORALES DE INTECO Y DEL CLIENTE.  Cada parte se hará responsable ' \
                            'de asegurar y mantener vigente las planillas de todos sus empleados. El cliente no tendrá relación ' \
                            'jerárquica, ni impondrá horarios, ni pagará dinero alguno a los auditores o profesionales del INTECO. ' \
                            'INTECO será el único patrono de ellos, encargándose de pagarles sus salarios en forma puntual, ' \
                            'lo mismo que el cliente con el personal asignado a trabajar con los auditores de INTECO. De la misma ' \
                            'manera ambas partes se comprometen a asegurar a todos sus empleados ante la Caja Costarricense de ' \
                            'Seguro Social y el Instituto Nacional de Seguros, así como a realizar puntualmente los pagos mensuales ' \
                            'de las cuotas obrero-patronales y de las primas que respectivamente corresponda pagar. Igualmente ' \
                            'se harán cargo de pagarles por su exclusiva cuenta todos los extremos laborales que les correspondan ' \
                            'durante y al finalizar la obra, de conformidad con lo prescrito en la legislación laboral costarricense. ' \
                            'En todo momento deberán mantener las pólizas del INS y las obligaciones con la CCSS al día, y realizar ' \
                            'los pagos puntualmente.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.	GENERALIDADES O MISCELÁNEOS. En caso que la oferta sea aceptada y el acuerdo empiece a regir, se ' \
                            'establecen las siguientes cláusulas contractuales, sin perjuicio de las cláusulas del acuerdo ' \
                            '(contrato), en cuanto a particularidades y otros temas de importancia, que junto con los documentos ' \
                            'de información preliminar, formarán un solo instrumento contractual.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.1.	NUEVAS NEGOCIACIONES ENTRE LAS PARTES. Cualquier solicitud del cliente fuera de los parámetros ' \
                            'establecidos por este instrumento, deberá hacerlo a INTECO, quien se obliga a la brevedad posible a ' \
                            'también por escrito, a resolver la misma, en caso de que se acepte alguna modificación, aclaración o ' \
                            'especificación a este instrumento la misma debe efectuarse mediante acuerdo realizado por escrito y ' \
                            'firmado por ambas partes.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.2.	RENUNCIA A RECLAMAR LA NULIDAD DEL CONTRATO. EL CLIENTE reconoce como válida y correcta la ' \
                            'información que le fue proporcionada a INTECO, así como la que se indica en este documento y en los ' \
                            'ANEXOS, por lo cual, desde este momento renuncia a cualquier acción de nulidad y de daños y perjuicios ' \
                            'derivada de dicha información, aceptando que su voluntad y consentimiento se expresan con la firma que' \
                            ' pone al pie de este documento, y en cada una de las páginas y ANEXOS.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.3.	CAUSAS DE VENCIMIENTO ANTICIPADO DEL PLAZO DEL CONTRATO.- Serán causas de vencimiento ' \
                            'anticipado del plazo de vigencia del presente contrato las siguientes:' \
                          + '<br/>' \
                          + 'i.	Que cualquier parte viole los términos de algunos de los documentos que forman este instrumento' \
                          + '<br/>' \
                          + 'ii.	Que EL CLIENTE se encuentre en mora en cualquiera de sus obligaciones de pago que contraen ' \
                            'con motivo de este instrumento' \
                          + '<br/>' \
                          + 'iii.	Que EL CLIENTE venda o distribuya o comercialice productos y/o servicios fuera de los términos ' \
                            'de la certificación de acuerdo a este documento' \
                          + '<br/>' \
                          + 'iv.	Que el cliente realice actos que atenten contra la certificación o los intereses de INTECO' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.4.	PACTO COMISORIO.- Si alguna de las partes incurre en incumplimiento en alguna de sus ' \
                            'obligaciones contenidas en este instrumento, la otra podrá considerarlo resuelto de pleno derecho, ' \
                            'sin necesidad de declaración judicial y en su caso accionar por los daños y perjuicios sufridos.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.5.	ALCANCE DE LOS TÍTULOS DE LAS CLÁUSULAS.- Las partes establecen que lo establecido en la ' \
                            'presente oferta y el acuerdo, así como la información previa entregada, expresa todo lo acordado ' \
                            'por las partes y que los títulos de cada cláusula únicamente fueron establecidos para facilitar la ' \
                            'lectura del contrato,  por lo que se debe de estar a lo expresamente acordado por las partes en el ' \
                            'clausulado respectivo.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.6.	MODIFICACIONES AL CONTRATO.- Cualquier modificación que las partes deseen realizar al contenido ' \
                            'del presente documento, deberá efectuarse mediante acuerdo realizado por escrito y firmado por el ' \
                            'Representante Legal de ambas partes.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.7.	DOMICILIOS CONVENCIONALES.- Las partes señalan como domicilios convencionales para recibir ' \
                            'todo tipo de documentos, notificaciones y demás comunicaciones los señalados al inicio de este ' \
                            'instrumento.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.8.	JURISDICCIÓN.- Para la interpretación, cumplimiento y ejecución del presente documento, ' \
                            'las partes convienen en someterse expresamente a las Leyes de Costa Rica, haciendo renuncia expresa ' \
                            'de cualquier otro fuero que pudiere corresponderles por razón de su domicilio presente o futuro, o ' \
                            'que por cualquier otra razón pudiera corresponderles.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.9.	NEGOCIACIÓN, CONCILIACIÓN Y ARBITRAJE:  En caso de diferencias, conflictos o disputas ' \
                            'relacionadas con la ejecución, incumplimiento, interpretación o cualquier otro aspecto derivado ' \
                            'de todos los documentos que forman este instrumento, y de las operaciones que como consecuencia del ' \
                            'mismo se realicen, las partes, de conformidad con los artículos cuarenta y uno y cuarenta y tres de ' \
                            'la Constitución Política, y la Ley sobre Resolución Alternativa de Conflictos y Promoción de la Paz ' \
                            'Social, número 7.727, ambas partes renuncian en este acto expresamente a la jurisdicción ordinaria y ' \
                            'acuerdan resolver el conflicto conforme al siguiente procedimiento:' \
                          + '<br/>' \
                          + 'i.	Compromiso de Negociación: las partes acuerdan acudir en primera instancia a un proceso de ' \
                            'negociación en donde ambas partes tratan de resolver el problema o conflicto entre sí, sin la ' \
                            'intervención de un tercero.' \
                          + '<br/>' \
                          + 'ii.	Compromiso de Conciliación: las partes acuerdan acudir en segunda instancia al proceso de ' \
                            'conciliación establecido en la reglamentación del Centro de Conciliación y Arbitraje de la Cámara ' \
                            'de Comercio de Costa Rica, designándose como mediador unipersonal a quien por turno corresponda, de ' \
                            'la lista que lleva la Dirección de dicho Centro. ' \
                          + '<br/>' \
                          + 'iii.	Compromiso Arbitral: en caso de que el asunto no sea resuelto en un máximo de dos audiencias ' \
                            'de conciliación, o en caso de que no se verifiquen las sesiones por ausencia de alguna de las partes, ' \
                            'el asunto o controversia será resuelto mediante un arbitraje de derecho que dictará un tribunal ' \
                            'integrado por tres miembros, uno que elegirá cada parte, y un tercero que elegirá el Centro y que ' \
                            'será quien presidirá el tribunal, todos elegidos de la lista que al efecto mantenga el Centro. ' \
                          + '<br/>' \
                          + 'iv.	El arbitraje se regirá por la legislación vigente y por la normativa dispuesta al efecto por ' \
                            'el Centro de Conciliación y Arbitraje de la Cámara de Comercio de Costa Rica, a cuyas normas las ' \
                            'partes se someten en forma incondicional. El laudo será definitivo e inapelable, en él se impondrá ' \
                            'el pago de las costas a cargo de la parte perdedora y producirá cosa juzgada material, salvo por los ' \
                            'recursos de revisión y de nulidad. Queda entendido que tanto la mediación como el arbitraje podrán ser ' \
                            'solicitados por cualesquiera de las partes. En caso de que en el momento en que deba resolverse el ' \
                            'conflicto, el Centro de Conciliación y Arbitraje de la Cámara de Comercio de Costa Rica no esté ' \
                            'prestando los servicios anteriormente referidos, el conflicto se resolverá ante el Centro Internacional' \
                            ' de Conciliación y Arbitraje (CICA) de la Cámara de Comercio Costarricense Norteamericana (AMCHAM), de ' \
                            'conformidad con lo anteriormente establecido, bajo la normativa vigente en dicho Centro.'

            en_phrase = 'Hereby, the applicant,' + ' ' + nom + ' ' + 'with' + ' ' + nif + ' ' + 'and registered address' + ' ' + addr + ' ' \
                                                                                                                                        ',llegally represented by' + ' ' + user_nom + ',personal identification number' + ' ' + user_id + \
                        ', in its capacity as' + ' ' + pos + ',  accepts in all its terms the offer number' + ' ' + pur_num + ', ' \
                                                                                                                              'verifies the accuracy of its data and declares to know and be bound to comply with what is specified in section 5 of this document and in Annex 1' \
                        + '<br/>' \
                        + '<br/>' \
                        + ' ' + 'After reading the present offer, the parties find it in accordance with its terms and sign it in proof of acceptance, in the place and date expressed therein.' \
                                ' ' \
                                'Signed in' + ' ' +'............'+ ' ' + ',' + 'at' + ' ' +'.....................'+ ' ' + 'hours of' \
                        + ' ' +'.................'+ ' ' + ',' + ' ' +'.............'+ ',' + ' ' +'.............'+ '.' + '<br/>' \
                        + '<br/>' \
                        + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_firm_ra + '&emsp;' + '&emsp;' + '&emsp;' + nom_dic_ra + '<br/>' \
                        + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_dic + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_firm

            if eng.en_temp == True:
                record.condition = en_phrase
            else:
                if record.note and self.serv_required_fi == True:
                    record.condition = phrase
                else:
                    record.condition = phrase+phrase_cond

    def buttons_vals(self):
        import calendar

        eng = self.env['sale.order.template'].search([('id', '=', self.sale_order_template_id.id)])
        for record in self:
            emp_spc = ' '
            nom = ''
            nif = ''
            addr = ''
            if record.partner_id:
                if record.partner_id.contact_name:
                    if record.partner_id.second_last_name:
                        nom = (record.partner_id.contact_name + ' ' + record.partner_id.contact_last_name + ' ' + record.partner_id.second_last_name)
                    else:
                        nom = (record.partner_id.contact_name + ' ' + record.partner_id.contact_last_name)
                else:
                    nom = str(record.partner_id.name)
                nif = (record.partner_id.vat or ' ')
                addr = (record.partner_id.street or ' ')
                user_province = str(record.env.user.city or ' ')

            user_id = str(record.signature_id or '')
            pur_num = str(record.name)
            pos = str(record.signature_pos or '')
            user_nom = str(record.sales_contacts.name or '')

            nom_firm = '(Nombre Representante legal, del cliente)'
            en_nom_firm = '(Name of the legal representative of the client)'
            nom_firm_ra = '_______________________________________'
            nom_dic = '(Nombre Director Ejecutivo de INTECO)'
            en_nom_dic = '(Name of INTECO Executive Director)'
            nom_dic_ra = '_______________________________________'

            # name_year = {
            #     'January': 'Enero',
            #     'February': 'Febrero',
            #     'March': 'Marzo',
            #     'April': 'Abril',
            #     'May': 'Mayo',
            #     'June': 'Junio',
            #     'July': 'Julio',
            #     'August': 'Agosto',
            #     'September': 'Septiembre',
            #     'October': 'Octubre',
            #     'November': 'Noviembre',
            #     'December': 'Diciembre',
            #     'january': 'Enero',
            #     'february': 'Febrero',
            #     'march': 'Marzo',
            #     'april': 'Abril',
            #     'may': 'Mayo',
            #     'june': 'Junio',
            #     'july': 'Julio',
            #     'august': 'Agosto',
            #     'september': 'Septiembre',
            #     'october': 'Octubre',
            #     'november': 'Noviembre',
            #     'december': 'Diciembre',
            #     'enero': 'January',
            #     'febrero': 'February',
            #     'marzo': 'March',
            #     'abril': 'April',
            #     'mayo': 'May',
            #     'junio': 'June',
            #     'julio': 'July',
            #     'agosto': 'August',
            #     'septiembre': 'September',
            #     'octubre': 'October',
            #     'noviembre': 'November',
            #     'diciembre': 'December',
            #     'Enero': 'January',
            #     'Febrero': 'February',
            #     'Marzo': 'March',
            #     'Abril': 'April',
            #     'Mayo': 'May',
            #     'Junio': 'June',
            #     'Julio': 'July',
            #     'Agosto': 'August',
            #     'Septiembre': 'September',
            #     'Octubre': 'October',
            #     'Noviembre': 'November',
            #     'Diciembre': 'December'
            # }

            phrase = 'Por la presente, el cliente,' + ' ' + nom + ' ' + 'con cédula' + ' ' + nif + ' ' + 'y domicilio social' + ' ' + addr + ' ' \
                                                                                                                                             ',representada legalmente por' + ' ' + user_nom + ',número de identificación personal' + ' ' + user_id + \
                     ', en su condición de' + ' ' + pos + ',  acepta en todos sus términos la oferta número' + ' ' + pur_num + ', ' \
                                                                                                                               'verifica la exactitud de sus datos y declara conocer y obligarse a cumplir lo especificado en ' \
                                                                                                                               'la sección 5 de este documento y en el Anexo 1.' \
                     + '<br/>' \
                     + '<br/>' \
                     + ' ' + 'Leída la presente oferta, las partes la encuentran conforme en todos sus términos y la firman en ' \
                             'prueba de aceptación, en el lugar y fecha expresados en el mismo.' \
                             ' ' \
                             'Firmado en' + ' ' +'.............'+ ' ' + ',' + 'a las' + ' ' +'..............'+ ' ' + 'horas del' \
                     + ' ' +'.............'+ ' ' + 'de' + ' ' +'...............'+ ' ' + 'de' + ' ' +'............'+ '.' + '<br/>' \
                     + '<br/>' \
                     + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_firm_ra + '&emsp;' + '&emsp;' + '&emsp;' + nom_dic_ra + '<br/>' \
                     + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_dic + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_firm

            phrase_cond = '<br/>' \
                          + '<br/>' \
                          + '<br/>' \
                          + 'Anexo 1' \
                          + '<br/>' \
                          + 'Condiciones legales' \
                          + '<br/>' \
                          + '<br/>' \
                          + '1.	DERECHOS DE AUTOR. Todo el trabajo realizado por los auditores culminará en la certificación ' \
                            'respectiva que se otorgue al cliente, en cuyo caso los derechos de autor corresponderán a las personas ' \
                            'físicas que participen del proceso y los derechos patrimoniales a INTECO. La información que entregue el ' \
                            'cliente, no formará parte de esos derechos.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.	CONFIDENCIALIDAD Y SECRETO PROFESIONAL. Las cláusulas y estipulaciones de esta oferta y del acuerdo ' \
                            'se inspiran en los más depurados principios de lealtad, equidad y buena fe, que recíprocamente guardan y ' \
                            'guardarán las partes y, en consecuencia, dichas cláusulas y estipulaciones serán de observancia obligatoria ' \
                            'para los efectos de su interpretación y aplicación. Cada parte se obliga con la otra y por todo el tiempo ' \
                            'que dure este contrato y más allá del mismo una vez que haya finalizado, a lo siguiente: ' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.1.	No comunicar, divulgar, suministrar o de cualquier forma poner a disposición de persona alguna, ' \
                            'ya sea de forma directa o indirecta Información de recibida por las partes. Se exceptúa de lo anterior:' \
                          + '<br/>' \
                          + 'i.	Si dicha divulgación es requerida por aplicación de disposiciones legales o por orden judicial u ' \
                            'otra orden coactiva similar' \
                          + '<br/>' \
                          + 'ii.	Cuando las partes expresamente lo autoricen por escrito. ' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.2.	No hacer manifestaciones públicas sobre el contenido este Contrato, sin el consentimiento ' \
                            'previo y por escrito de la otra parte.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '2.3.	Se reconoce que cada parte tendrá derecho a que se ordene el cumplimiento específico en caso' \
                            ' de un incumplimiento de este acuerdo de confidencialidad, además de cualquier otro derecho o recurso' \
                            ' de conformidad con la ley, sea un derecho a una compensación por daños o perjuicios.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '3.	DENUNCIAS POR DERECHOS DEL CONSUMIDOR, CIVILES, PENALES Y/O ADMINISTRATIVOS. INTECO no tendrá ' \
                            'ninguna responsabilidad final por los productos y/o servicios que el cliente llegue a comercializar, ' \
                            'ya sean derechos del consumidor, civiles, penales y/o administrativos, temas que deberá enfrentar el ' \
                            'cliente por sí solo. ' \
                          + '<br/>' \
                          + '<br/>' \
                          + '4.	RESPONSABILIDADES SOCIALES Y LABORALES DE INTECO Y DEL CLIENTE.  Cada parte se hará responsable ' \
                            'de asegurar y mantener vigente las planillas de todos sus empleados. El cliente no tendrá relación ' \
                            'jerárquica, ni impondrá horarios, ni pagará dinero alguno a los auditores o profesionales del INTECO. ' \
                            'INTECO será el único patrono de ellos, encargándose de pagarles sus salarios en forma puntual, ' \
                            'lo mismo que el cliente con el personal asignado a trabajar con los auditores de INTECO. De la misma ' \
                            'manera ambas partes se comprometen a asegurar a todos sus empleados ante la Caja Costarricense de ' \
                            'Seguro Social y el Instituto Nacional de Seguros, así como a realizar puntualmente los pagos mensuales ' \
                            'de las cuotas obrero-patronales y de las primas que respectivamente corresponda pagar. Igualmente ' \
                            'se harán cargo de pagarles por su exclusiva cuenta todos los extremos laborales que les correspondan ' \
                            'durante y al finalizar la obra, de conformidad con lo prescrito en la legislación laboral costarricense. ' \
                            'En todo momento deberán mantener las pólizas del INS y las obligaciones con la CCSS al día, y realizar ' \
                            'los pagos puntualmente.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.	GENERALIDADES O MISCELÁNEOS. En caso que la oferta sea aceptada y el acuerdo empiece a regir, se ' \
                            'establecen las siguientes cláusulas contractuales, sin perjuicio de las cláusulas del acuerdo ' \
                            '(contrato), en cuanto a particularidades y otros temas de importancia, que junto con los documentos ' \
                            'de información preliminar, formarán un solo instrumento contractual.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.1.	NUEVAS NEGOCIACIONES ENTRE LAS PARTES. Cualquier solicitud del cliente fuera de los parámetros ' \
                            'establecidos por este instrumento, deberá hacerlo a INTECO, quien se obliga a la brevedad posible a ' \
                            'también por escrito, a resolver la misma, en caso de que se acepte alguna modificación, aclaración o ' \
                            'especificación a este instrumento la misma debe efectuarse mediante acuerdo realizado por escrito y ' \
                            'firmado por ambas partes.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.2.	RENUNCIA A RECLAMAR LA NULIDAD DEL CONTRATO. EL CLIENTE reconoce como válida y correcta la ' \
                            'información que le fue proporcionada a INTECO, así como la que se indica en este documento y en los ' \
                            'ANEXOS, por lo cual, desde este momento renuncia a cualquier acción de nulidad y de daños y perjuicios ' \
                            'derivada de dicha información, aceptando que su voluntad y consentimiento se expresan con la firma que' \
                            ' pone al pie de este documento, y en cada una de las páginas y ANEXOS.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.3.	CAUSAS DE VENCIMIENTO ANTICIPADO DEL PLAZO DEL CONTRATO.- Serán causas de vencimiento ' \
                            'anticipado del plazo de vigencia del presente contrato las siguientes:' \
                          + '<br/>' \
                          + 'i.	Que cualquier parte viole los términos de algunos de los documentos que forman este instrumento' \
                          + '<br/>' \
                          + 'ii.	Que EL CLIENTE se encuentre en mora en cualquiera de sus obligaciones de pago que contraen ' \
                            'con motivo de este instrumento' \
                          + '<br/>' \
                          + 'iii.	Que EL CLIENTE venda o distribuya o comercialice productos y/o servicios fuera de los términos ' \
                            'de la certificación de acuerdo a este documento' \
                          + '<br/>' \
                          + 'iv.	Que el cliente realice actos que atenten contra la certificación o los intereses de INTECO' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.4.	PACTO COMISORIO.- Si alguna de las partes incurre en incumplimiento en alguna de sus ' \
                            'obligaciones contenidas en este instrumento, la otra podrá considerarlo resuelto de pleno derecho, ' \
                            'sin necesidad de declaración judicial y en su caso accionar por los daños y perjuicios sufridos.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.5.	ALCANCE DE LOS TÍTULOS DE LAS CLÁUSULAS.- Las partes establecen que lo establecido en la ' \
                            'presente oferta y el acuerdo, así como la información previa entregada, expresa todo lo acordado ' \
                            'por las partes y que los títulos de cada cláusula únicamente fueron establecidos para facilitar la ' \
                            'lectura del contrato,  por lo que se debe de estar a lo expresamente acordado por las partes en el ' \
                            'clausulado respectivo.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.6.	MODIFICACIONES AL CONTRATO.- Cualquier modificación que las partes deseen realizar al contenido ' \
                            'del presente documento, deberá efectuarse mediante acuerdo realizado por escrito y firmado por el ' \
                            'Representante Legal de ambas partes.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.7.	DOMICILIOS CONVENCIONALES.- Las partes señalan como domicilios convencionales para recibir ' \
                            'todo tipo de documentos, notificaciones y demás comunicaciones los señalados al inicio de este ' \
                            'instrumento.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.8.	JURISDICCIÓN.- Para la interpretación, cumplimiento y ejecución del presente documento, ' \
                            'las partes convienen en someterse expresamente a las Leyes de Costa Rica, haciendo renuncia expresa ' \
                            'de cualquier otro fuero que pudiere corresponderles por razón de su domicilio presente o futuro, o ' \
                            'que por cualquier otra razón pudiera corresponderles.' \
                          + '<br/>' \
                          + '<br/>' \
                          + '5.9.	NEGOCIACIÓN, CONCILIACIÓN Y ARBITRAJE:  En caso de diferencias, conflictos o disputas ' \
                            'relacionadas con la ejecución, incumplimiento, interpretación o cualquier otro aspecto derivado ' \
                            'de todos los documentos que forman este instrumento, y de las operaciones que como consecuencia del ' \
                            'mismo se realicen, las partes, de conformidad con los artículos cuarenta y uno y cuarenta y tres de ' \
                            'la Constitución Política, y la Ley sobre Resolución Alternativa de Conflictos y Promoción de la Paz ' \
                            'Social, número 7.727, ambas partes renuncian en este acto expresamente a la jurisdicción ordinaria y ' \
                            'acuerdan resolver el conflicto conforme al siguiente procedimiento:' \
                          + '<br/>' \
                          + 'i.	Compromiso de Negociación: las partes acuerdan acudir en primera instancia a un proceso de ' \
                            'negociación en donde ambas partes tratan de resolver el problema o conflicto entre sí, sin la ' \
                            'intervención de un tercero.' \
                          + '<br/>' \
                          + 'ii.	Compromiso de Conciliación: las partes acuerdan acudir en segunda instancia al proceso de ' \
                            'conciliación establecido en la reglamentación del Centro de Conciliación y Arbitraje de la Cámara ' \
                            'de Comercio de Costa Rica, designándose como mediador unipersonal a quien por turno corresponda, de ' \
                            'la lista que lleva la Dirección de dicho Centro. ' \
                          + '<br/>' \
                          + 'iii.	Compromiso Arbitral: en caso de que el asunto no sea resuelto en un máximo de dos audiencias ' \
                            'de conciliación, o en caso de que no se verifiquen las sesiones por ausencia de alguna de las partes, ' \
                            'el asunto o controversia será resuelto mediante un arbitraje de derecho que dictará un tribunal ' \
                            'integrado por tres miembros, uno que elegirá cada parte, y un tercero que elegirá el Centro y que ' \
                            'será quien presidirá el tribunal, todos elegidos de la lista que al efecto mantenga el Centro. ' \
                          + '<br/>' \
                          + 'iv.	El arbitraje se regirá por la legislación vigente y por la normativa dispuesta al efecto por ' \
                            'el Centro de Conciliación y Arbitraje de la Cámara de Comercio de Costa Rica, a cuyas normas las ' \
                            'partes se someten en forma incondicional. El laudo será definitivo e inapelable, en él se impondrá ' \
                            'el pago de las costas a cargo de la parte perdedora y producirá cosa juzgada material, salvo por los ' \
                            'recursos de revisión y de nulidad. Queda entendido que tanto la mediación como el arbitraje podrán ser ' \
                            'solicitados por cualesquiera de las partes. En caso de que en el momento en que deba resolverse el ' \
                            'conflicto, el Centro de Conciliación y Arbitraje de la Cámara de Comercio de Costa Rica no esté ' \
                            'prestando los servicios anteriormente referidos, el conflicto se resolverá ante el Centro Internacional' \
                            ' de Conciliación y Arbitraje (CICA) de la Cámara de Comercio Costarricense Norteamericana (AMCHAM), de ' \
                            'conformidad con lo anteriormente establecido, bajo la normativa vigente en dicho Centro.'

            en_phrase = 'Hereby, the applicant,' + ' ' + nom + ' ' + 'with' + ' ' + nif + ' ' + 'and registered address' + ' ' + addr + ' ' \
                                                                                                                                        ',llegally represented by' + ' ' + user_nom + ',personal identification number' + ' ' + user_id + \
                        ', in its capacity as' + ' ' + pos + ',  accepts in all its terms the offer number' + ' ' + pur_num + ', ' \
                                                                                                                              'verifies the accuracy of its data and declares to know and be bound to comply with what is specified in section 5 of this document and in Annex 1' \
                        + '<br/>' \
                        + '<br/>' \
                        + ' ' + 'After reading the present offer, the parties find it in accordance with its terms and sign it in proof of acceptance, in the place and date expressed therein.' \
                                ' ' \
                                'Signed in' + ' ' +'.........'+ ' ' + ',' + 'at' + ' ' +'..................'+ ' ' + 'hours of' \
                        + ' ' +'..............'+ ' ' + ',' + ' ' +'..............'+ ',' + ' ' +'...........'+ '.' + '<br/>' \
                        + '<br/>' \
                        + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + nom_firm_ra + '&emsp;' + '&emsp;' + '&emsp;' + nom_dic_ra + '<br/>' \
                        + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + en_nom_dic + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + '&emsp;' + en_nom_firm

            if eng.en_temp == True:
                record.condition = en_phrase
            else:
                if record.note and self.serv_required_fi == True:
                    record.condition = phrase
                else:
                    record.condition = phrase + phrase_cond

    @api.onchange('sales_contacts')
    def get_contacts(self):
        if self.partner_id:
            for record in self.sales_contacts:
                self.signature_pos = record.function
                self.signature_id = record.vat

    def order_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        name_year = {
            'year_1': 'Año 1',
            'year_2': 'Año 2',
            'year_3': 'Año 3',
            'year_4': 'Año 4',
            'year_5': 'Año 5'
        }

        self.ensure_one()
        res = super(ChangeSaleOrderConditions, self).order_lines_layouted()
        for record in res[0]:
            if 'lines' in record:
                year = []
                year_names = []
                for rec in record['lines']:
                    if rec.year_section not in year_names:
                        if rec.year_section in name_year:
                            year.append({'year': rec.year_section, 'name': name_year[rec.year_section]})
                            year_names.append(rec.year_section)
                record['year_section'] = year

        return res


class Sale_Order_Inherit(models.Model):
    _inherit = "sale.order.line"
    _description = 'añadir campos al tree order line'

    year_section = fields.Selection([
        ('year_1', 'Año 1'),
        ('year_2', 'Año 2'),
        ('year_3', 'Año 3'),
        ('year_4', 'Año 4'),
        ('year_5', 'Año 5')
    ], string='Sección', default='year_1')
    layout_category_id = fields.Many2one('sale.layout_category', string='Section')

    required_fi = fields.Boolean(string='Condición campos requeridos', compute='calc_group')
    payment_date = fields.Date(string='Fecha Estimada del proceso')
    analytic_account_default = fields.Many2one("account.analytic.account", string="Cuenta Analítica", tracking=True)

    @api.onchange('product_uom_qty')
    def calc_group(self):
        for record in self:
            if record.order_id.sale_order_template_id.categ_template == 'evac_ser':
                record.required_fi = True
            else:
                record.required_fi = False


    @api.onchange('product_template_id')
    def _onchange_product_account(self):
        for record in self:
            if record.product_template_id:
                if record.product_template_id.product_analytic_account:
                    an_account = record.product_template_id.product_analytic_account
                    record.analytic_account_default = an_account
                else:
                    if record.product_template_id.categ_id.analytic_account_def:
                        an_account = record.product_template_id.categ_id.analytic_account_def
                        record.analytic_account_default = an_account
                    else:
                        record.analytic_account_default = ''
            else:
                record.analytic_account_default = ''


    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """

        self.ensure_one()

        eng = self.env['sale.order.line'].search([('order_id', '=', self.order_id.id)])
        for record in eng:
            if record.product_template_id:
                if record.analytic_account_default:
                    pass
                else:
                    if record.product_template_id.product_analytic_account:
                        an_account = record.product_template_id.product_analytic_account
                        record.analytic_account_default = an_account
                    else:
                        if record.product_template_id.categ_id.analytic_account_def:
                            an_account = record.product_template_id.categ_id.analytic_account_def
                            record.analytic_account_default = an_account
                        else:
                            record.analytic_account_default = False
            else:
                record.analytic_account_default = False

        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.analytic_account_default.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res

class Remove_condition(models.Model):
    _inherit = "res.partner"
    _description = 'remueve la condición de no repetir correos en el modulo de contactos'

    # contact_id = fields.Char(string="Cédula", required=False, )

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

class SaleLayoutCategory(models.Model):
    _name = 'sale.layout_category'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', required=True, default=10)
    subtotal = fields.Boolean('Add subtotal', default=True)
    pagebreak = fields.Boolean('Add pagebreak')

class Sale_Prod_Cat_Inherit(models.Model):
    _inherit = "sale.order.template"

    en_temp = fields.Boolean(string="Plantilla en Inglés?")
    dse_temp = fields.Boolean(string="Plantilla DSE?")
    sale_rec = fields.Char(string="Registro")
    sale_ver = fields.Char(string="Número de versión")
    categ_template = fields.Selection(string="Categoría de plantilla", selection=[
        ('norm', 'Normalización'),
        ('evac_ser', 'Servicios de Evaluación'),
        ('afil', 'Afiliados'),
        ('event', 'Eventos'),
        ('formation','Formación'),
        ('idl', 'i+d+l')
    ], tracking=True)

class SaleProductInherit(models.Model):
    _inherit = "sale.order.option"

    sale_required_fi = fields.Boolean(string='Condición campos requeridos')
    required_fi = fields.Boolean(string='Condición campos requeridos', compute='calc_group')

    def calc_group(self):
        if self.user_has_groups('dfx_product_changes.norm_group') or \
                self.user_has_groups('dfx_product_changes.serv_evac_group') or \
                self.user_has_groups('dfx_product_changes.afil_group') or \
                self.user_has_groups('dfx_product_changes.event_group') or \
                self.user_has_groups('dfx_product_changes.formac_group') or \
                self.user_has_groups('dfx_product_changes.idl_group'):
            self.required_fi = True