# -*- coding: utf-8 -*-

{
    'name': 'Módulo de Cambios en productos',
    'version': '07.05.21.1',
    'author': 'DelfixCR',
    'license': 'OPL-1',
    'support': 'soporte@delfixcr.com',
    'website': 'https://www.delfixcr.com',
    'category': 'Product',
    'description':
        '''
        Cambios en Productos
        ''',
    'depends': [
        'base',
        'purchase',
        'sale',
        'mail',
        'inteco',
        'website_sale',
        # 'cr_electronic_invoice'
    
    ],
    'data': [
        'data/ir_actions_data.xml',
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/product_inherit_view.xml',
        'wizard/product_wizard_view.xml'
    ],
    'installable': True,
}
