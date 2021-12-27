# -*- coding: utf-8 -*-

{
	'name': 'Módulo cambios en ventas',
	'version': '21.07.21.1',
	'author': 'DelfixCR',
	'license': 'OPL-1',
	'support': 'soporte@delfixcr.com',
	'website': 'https://www.delfixcr.com',
	'category': 'Sale',
	'description':
		'''
		Cambios en Ventas.
		''',
	'depends': [
		'base',
		'mail',
		'sale',
		'inteco',
		'dfx_product_changes',

	],
	'data': [
		'security/ir.model.access.csv',
		'views/sale_order_in_view.xml',
	],
	'installable': True,
}
