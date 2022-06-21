# -*- coding: utf-8 -*-

{
    'name': 'Modulo de cambios en facturación',
    'version': '11.08.21.1',
    'author': 'DelfixCR',
    'license': 'OPL-1',
    'support': 'soporte@delfixcr.com',
    'website': 'https://www.delfixcr.com',
    'category': 'Account',
    'description':
        '''
        Cambios en Contabilidad.
        ''',
    'depends': [
        'account',
        'cr_electronic_invoice',
    ],
    'data': [
        'security/res_groups.xml',
        'views/account_invoice_inherit_view.xml',
        'views/res_company_view.xml',
        'data/cron.xml',
        'data/mail_template_electronic_invoice_rejected.xml',
        'data/account_journal.xml',
        'data/late_mail_template_electronic_invoice.xml',
    ],
    'installable': True,
}
