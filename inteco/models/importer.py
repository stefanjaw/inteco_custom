# -*- coding: utf-8 -*-

import time
import csv
import base64
import re
from tempfile import TemporaryFile
from collections import defaultdict
from odoo import fields, models, api, _


class Sector(models.Model):
    _name = 'inteco.importer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Importer used to created the records related with the laws'
    _rec_name = 'models_available'

    csv_file = fields.Binary(
        help='CSV File used to created records. This file has to follow a'
        'specific template depending of model that the records belong '
    )
    models_available = fields.Selection(
        [('committee', 'Committee'),
         ('ics', 'ICS'),
         ('product', 'Product')],
        help='Model which records belong'
    )
    log_errors = fields.Char(string="log_errors", required=False, )
    
    #TODO QUITAR @api.multi
    def import_records(self):
        """Importing records to their corresponding model
        """
        self.ensure_one()
        methods = {
            'committee': self.import_committee,
            'product': self.import_products,
            'ics': self.import_ics,
        }
        fileobj = TemporaryFile('w+')
        content = base64.b64decode(self.csv_file).decode('utf-8', 'ignore')
        fileobj.write(content)
        fileobj.seek(0)
        read_fid = csv.DictReader(fileobj, delimiter=',', quotechar='"')
        if not read_fid or not self.check_file(self.models_available, read_fid.fieldnames):
            return True
        self.log_errors = ''
        methods.get(self.models_available, lambda a: None)(read_fid)
        name = self.models_available + '_' + time.strftime('%Y_%m_%d_%H_%M_%S')
        attach = [(name + '.csv', content)]
        attach += self.log_errors and [(name + '.log', self.log_errors)] or ()
        self.message_post(body=_('CSV File Used'), attachments=attach)

    @api.model
    # @staticmethod
    def check_file(self, model, lfields):
        """Checking if the file has the values expected
        :param model: Model which records in file belong
        :type model: str
        :param lfields: Fields which the file contains
        :type lfields: dict_keys

        :return: The result if the file contains the expected values
        :rtype: bool
        """
        expected = {
            'committee': ['code', 'id', 'name', 'type', 'identifier',
                          'parent_id', 'letter_id', 'sec_code', 'sec_name',
                          'isinter', 'committee', 'type_part', 'ignore', ''],
            'ics': ['code', 'pt_PT', 'en_US', 'es_CR', 'ignore', ''],
            'product': ['previous_code', 'id', 'process', 'committee_id',
                        'prefix_id', 'sector_id', 'short_code',
                        'edition_year', 'modifier', 'modifier_num',
                        'modifier_year', 'default_code', 'name',
                        'application_field', 'correspondence_ids',
                        'public_categ_ids', 'ics_ids', 'edition', 'approval',
                        'standard_reference', 'pages', 'list_price',
                        'standard_reference_inv', 'state', 'replaced_by',
                        'part_one', 'part_two', 'part_tree', 'ignore', '']

        }.get(model, [])
        result = all([False for i in lfields if i not in expected])
        return result

    #TODO QUITAR @api.multi
    def import_ics(self, dict_file):
        """Creating / Updating ICS
        :param dict_file: File with the data to be created/updated
        :type dict_file: DictReader
        """
        ics_model = self.env['inteco.ics']
        translation_model = self.env['ir.translation']
        ifields = ['name', 'code', 'parent_id/id']
        tfields = ['id', 'src', 'lang', 'res_id', 'source', 'name', 'value',
                   'type']
        for row in dict_file:
            ccode = row.get('code').lower().replace('.000', '')
            xml_id = ('__export__.inteco_ics_' + re.sub(r'\W+', '_', ccode))
            code = ccode.split('.')
            parent = '_'.join(code[:len(code) - 1])
            parent = '__export__.inteco_ics_' + parent if parent else ''

            lst_ics = [[
              row.get('en_US'),
              code[-1],
              parent]]
            
            result = ics_model.load(ifields, lst_ics)

            self.log_errors += self._generate_log(result.get('messages'),
                                                  row.get('code'))
            res_id = result.get('ids')
            result = translation_model.load(
                tfields,
                [[xml_id + '_pt_PT',
                  row.get('en_US'),
                  'pt_PT',
                  res_id[0] if res_id else 0,
                  row.get('en_US'),
                  'inteco.ics,name',
                  row.get('pt_PT'),
                  'model']]
            )

            self.log_errors += self._generate_log(result.get('messages'),
                                                  'Portuguese translation')

            result = translation_model.load(
                tfields,
                [[xml_id + '_es_CR',
                  row.get('en_US'),
                  'es_CR',
                  res_id[0] if res_id else 0,
                  row.get('en_US'),
                  'inteco.ics,name',
                  row.get('es_CR'),
                  'model']]
            )

            self.log_errors += self._generate_log(result.get('messages'),
                                                  'Spanish translation')

    #TODO QUITAR @api.multi
    def import_committee(self, dict_file):
        """Creating / Updating Committees
        :param dict_file: File with the data to be created/updated
        :type dict_file: DictReader
        """
        committee_model = self.env['inteco.committee']
        mfields = ['id', 'name', 'type', 'identifier', 'parent_id/id',
                   'sector_id/id', 'international', 'international_committe',
                   'international_participation']

        parents = {}
        for row in dict_file:
            xml_id = ('__export__.inteco_committee_' + re.sub(r'\W+', '_', row.get('code')).lower())
            parents[row.get('id')] = xml_id
            sec_code = row.get('sec_code')
            
            lst_committe =  [[xml_id,
                              row.get('name'),
                              row.get('type'),
                              row.get('identifier').rjust(2, '0'),
                              parents.get(row.get('parent_id'), ''),
                              'inteco.sector_code_' + sec_code.lower() if sec_code else '',
                              row.get('isinter'),
                              row.get('committee'),
                              row.get('type_part')]]
            
            result = committee_model.load(mfields, lst_committe)
            self.log_errors += self._generate_log(result.get('messages'),
                                                  row.get('name'))

    #TODO QUITAR @api.multi
    def import_products(self, dict_file):
        """Creating / Updating Products
        :param dict_file: File with the data to be created/updated
        :type dict_file: DictReader
        """
        product_model = self.env['product.product']
        template_model = self.env['product.template']
        tfields = ['id', 'name', 'application_field', 'process', 'short_code',
                   'sector_id/id', 'committee_id', 'prefix_id',
                    'edition', 'year', 'public_categ_ids/id',
                   'correspondence_ids/id', 'categ_id/id', 'list_price',
                   'part_one', 'part_two', 'part_three', 'type']
        pfields = ['id', 'default_code', 'previous_code', 'pages', 'approval',
                   'state', 'replaced_by', 'product_tmpl_id',
                    'standards_ref' #'attribute_value_ids/id',
                   ]
        grouped = defaultdict(list)
        product_states = {
            'Eliminado': 'D',
            'Sustituido': 'R',
            'Vigente': 'C'
        }
        categories = {
            'producto': 'inteco.public_category_product',
            'guía': 'inteco.public_category_guide',
            'documento_normativo': 'inteco.public_category_normative',
            'método_de_ensayo': 'inteco.public_category_testing',
            'sistema_de_gestión': 'inteco.public_category_management',
            'vocabulario': 'inteco.public_category_vocabulary'
        }
        pt_name = ''
        for row in dict_file:
            modifier = row.get('modifier')
            xml_id = re.sub(r'/%s.*' % modifier if modifier else '','', row.get('default_code'))
            xml_id = re.sub(r'\W+', '_', xml_id).lower()
            obj_pt = template_model.search([('name', '=', row.get('default_code'))])
            pt = str(obj_pt.name)
            pt_name = str(obj_pt.id)
            grouped[pt].append(row)

        for xml_id in grouped:
            # txml_id = ('__export__.product_template_' + xml_id)
            txml_id = xml_id
            row = grouped[xml_id][0]
            categ_id = categories.get(
                re.sub(r'\W+', '_', row.get('public_categ_ids')).lower(),
                'inteco.public_category_type')
            correspondences = self.get_correspondence(
                row.get('correspondence_ids'))
            
            if row.get('committee_id'):
                # committe = ('__export__.inteco_committee_' + re.sub(r'\W+', '_', row.get('committee_id')).lower())
                obj = self.env['inteco.committee'].search([('name', '=', row.get('committee_id'))])
                committe = obj.name
            else:
                committe = ''
             
            if row.get('prefix_id'):
                # prefix = ('dfx_load_data_inteco.prefix_' + re.sub(r'\W+', '_', row.get('prefix_id')).lower().replace('í', 'i'))
                obj_prefix = self.env['inteco.prefix'].search([('name', '=', row.get('prefix_id'))])
                prefix = obj_prefix.name
            else:
                prefix = ''
            
            
            ics_2 = ','.join(['__export__.inteco_ics_' +re.sub(r'\W+', '_', i.strip()) for i in row.get('ics_ids').split(',') if i])
            
            ics = False
            if row.get('ics_ids'):
                lst_ics = ''
                cont = 1
                for i in row.get('ics_ids').split(','):
                    ics_id = self.env['inteco.ics'].search([('name', '=', i)])
                    if ics_id:
                        if cont == 1:
                            lst_ics += str(ics_id.id)
                            cont += 1
                        else:
                            lst_ics += ','+str(ics_id.id)
                ics = lst_ics or False

            # ','.join(['__export__.inteco_ics_' + re.sub(r'\W+', '_', i.strip())
            #           for i in row.get('ics_ids').split(',') if i])
                
            list_prod = [[txml_id,
              row.get('name').strip() or 'NO NAME',
              row.get('application_field'),
              row.get('process')[0] if row.get('process') else '',
              row.get('short_code'),
              ('inteco.sector_code_' + row.get('sector_id').lower() # TODO inteco.
               if re.match(r'[a-zA-Z]{1}$', row.get('sector_id')) else ''),
              committe,
              prefix,
              # ics_2,
              row.get('edition'),
              row.get('edition_year'),
              categ_id,
              correspondences,
              'inteco.product_category_1_1',
              row.get('list_price'),
              row.get('part_one'),
              row.get('part_two'),
              row.get('part_tree') or row.get('part_three'),
              'service']]
            
            result = template_model.sudo().with_context( {'create_product_product': True}).load(tfields, list_prod)
            self.log_errors += self._generate_log(result.get('messages'), row.get('default_code'))

            # for prod in grouped[xml_id]:
            #     # TODO corregir
            #     # attributes = self._generate_attribute_lines(
            #     #     prod.get('modifier'),
            #     #     prod.get('modifier_num'),
            #     #     prod.get('modifier_year'),
            #     #     xml_id)
            #     pxml_id = ('__export__.product_product_' +
            #                re.sub(r'\W+', '_',
            #                       prod.get('default_code')).lower())
            #
            #     result = product_model.sudo().load(
            #         pfields,
            #         [[pxml_id,
            #           prod.get('default_code'),
            #           prod.get('previous_code'),
            #           prod.get('pages'),
            #           prod.get('approval'),
            #           product_states.get(prod.get('state'), ''),
            #           '',  # prod.get('replaced_by'),
            #           pt_name,
            #           #False, #attributes, TODO corregir
            #           prod.get('standard_reference')]])
            #     self.log_errors += self._generate_log(result.get('messages'),
            #                                           row.get('default_code'))

    #TODO QUITAR @api.multi
    def get_correspondence(self, codes):
        """Creating or updating correspondences
        :param codes: Correspondences code related to product
        :type codes: str

        :return: The xml_id for each code
        :rtype: str"""
        if not codes or codes.strip() == 'N.A':
            return ''

        xml_ids = []
        organism_standard_model = self.env['inteco.organism.standard']
        cfields = ['id', 'name', 'organism_id/id']
        change_code = {
            'nch': 'inn',
            'gb': 'ccsa',
            'en': 'aenor',
            'a615': 'astm',
            'a588': 'astm',
            'a36': 'astm',
            'a572': 'astm',
            'pbi': 'bsi',
            'd': 'astm',
            'cac': 'cac_rcp',
            'ntp': 'indecopi',
            'as': 'sa',
            'nordom': 'indocal',
            'ntc': 'icontec',
            'nb': 'ibnorca',
            'can': 'csa',
            'guía': 'iso',
            'hd': 'aenor',
        }
        for code in codes.split(', '):
            orga_code = re.match(
                r'^\w+(/\w+)' if 'INTE' in code else r'^\w+', code.strip())
            orga_code = orga_code.group().lower().replace('/', '_')
            orga_code = (
                'inteco.organism_' + change_code.get(orga_code, orga_code)
                if orga_code else '')
            exists = self.env.ref(orga_code, False)
            self.log_errors += (
                _('The organism %s does not exist \n') % (
                    code if not exists else ''))
            nxml_id = ('__export__.inteco_organism_standard_' +
                       re.sub(r'\W+', '_', code).lower())
            result = organism_standard_model.load(
                cfields,
                [[nxml_id,
                  code,
                  orga_code]])
            self.log_errors += self._generate_log(result.get('messages'),
                                                  code)
            xml_ids += (nxml_id,) if not result.get('messages') else ()

        return ','.join(xml_ids)

    @api.model
    # @staticmethod
    def _generate_log(self, result, record):
        """Generate a readable log message indicating the reason why a product
        couldn't be created when it was trying to create itself
        :param result: Message which was returned by load method
        :type result: str
        :param record: Record name
        :param record: str
        """
        if not result:
            return ''
        message = _(
            'The record %s could not be created because <Br> %s \n') % (
                record, result[0].get('message'))
        return message

    @api.model
    def _generate_attribute_lines(self, modifier, modifier_number,
                                  modifier_year, template):
        """Create the attributes lines related to a template
        :param modifier: Name or code of modifier
        :type modifier: str
        :param modifier_number: Number of modifier
        :type modifier_number: int
        :param modifier_year: Year of modifier
        :type modifier_year: int
        :param template: xml_id of the template
        :type template: str

        :return: Attributes xml_ids
        :rtype: str
        """
        attribute_model = self.env['product.attribute.value']
        attrline_model = self.env['product.attribute.line'].with_context(
            {'update_many2many': True})
        amxml_id = 'inteco.modifier_attribute'
        amnxml_id = 'inteco.modifier_number_attribute'
        amyxml_id = 'inteco.modifier_year_attribute'
        atlfields = [
            'id', 'value_ids/id', 'product_tmpl_id/id', 'attribute_id/id']
        atfields = ['id', 'attribute_id/id', 'name']
        xml_ids = []
        t_id = ('__export__.product_template_' + template)
        if modifier:
            m_id = ('inteco.attribute_modifier_' +
                    re.sub(r'\W+', '_', modifier).lower())
            attrline_model.load(
                atlfields,
                [['__export__.inteco_attribute_modifier_' + template,
                  m_id, t_id, amxml_id]])
            xml_ids.append(m_id)

        if modifier_number:
            m_id = ('inteco.attribute_modifiernumber_' +
                    re.sub(r'\W+', '_', modifier_number).lower())
            attrline_model.load(
                atlfields,
                [['__export__.inteco_attribute_modifiernumber_' + template,
                  m_id, t_id, amnxml_id]])
            xml_ids.append(m_id)

        if modifier_year:
            m_id = ('__export__.inteco_attribute_modifieryear_' +
                    re.sub(r'\W+', '_', modifier_year).lower())
            attribute_model.load(
                atfields,
                [[m_id,
                  amyxml_id,
                  modifier_year]])

            attrline_model.load(
                atlfields,
                [['__export__.inteco_attribute_modifieryear_' + template,
                  m_id, t_id, amyxml_id]])
            xml_ids.append(m_id)

        return ','.join(xml_ids)
