from odoo import models, fields, api, _


class BudgetAccount(models.Model):
    _name = "budget.account"
    _description = 'Cuenta Presupuestaria'

    budget_name = fields.Char(string="Nombre")
    _rec_name = 'budget_name'