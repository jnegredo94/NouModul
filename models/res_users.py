from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"
    
    salesperson_route_ids = fields.One2many("factures.salesperson.routes", "salesperson_id", string="Salesperson Routes")
    