# -*- encoding: utf-8 -*-
{
    'name': 'Productos digitales, marca de agua',
    'version': '25.06.21.1',
    'summary': 'Cambios a productos digitales',
    'category': 'Website',
    'description': """Por medio de un Check en archivos adjuntos se habilita la marca de agua en documentos digitales""",
    'depends': [
        'base',
        'documents',
        'website_sale',
        'website_sale_digital',
        'inteco',
        'payment_credomatic',
        'website_sale',
        'payment'
    ],
    'installable': True,
    'data': [
        'views/assets.xml',
        'views/website_sale_digital.xml',
        'views/templates.xml',
        'views/sale_order_view.xml',
        'views/ir_attachment_view.xml',
        'report/report_watermark.xml',
    ],
}
