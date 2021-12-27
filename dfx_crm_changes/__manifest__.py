# -*- coding: utf-8 -*-

{
	'name': 'Módulo cambios en crm',
	'version': '30.07.21.1',
	'author': 'DelfixCR',
	'license': 'OPL-1',
	'support': 'soporte@delfixcr.com',
	'website': 'https://www.delfixcr.com',
	'category': 'Crm',
	'description':
		'''
		Cambios en crm.
		''',
	'depends': [
		'base',
		'mail',
		'crm',
		'inteco',
		'utm',
		'sale_crm',


	],
	'data': [
		'security/security_groups.xml',
		'security/ir.model.access.csv',
		'views/crm_changes_view.xml'
	],
	'installable': True,
}
