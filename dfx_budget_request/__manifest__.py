# -*- coding: utf-8 -*-

{
	'name': 'Módulo de Solicitudes de Presupuesto',
	'version': '07.07.21.1',
	'author': 'DelfixCR',
	'license': 'OPL-1',
	'support': 'soporte@delfixcr.com',
	'website': 'https://www.delfixcr.com',
	'category': 'Purchase',
	'description':
		'''
		Solicitud de Presupuesto Inteco.
		''',
	'depends': [
		'base',
		'purchase',
		'mail',
		'purchase_stock',
		'inteco',
		'account'

	],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/purchase_order_inherit_view.xml',
		'views/budget_and_cost.xml'
	],
	'installable': True,
}
