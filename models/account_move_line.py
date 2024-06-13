from odoo import fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    quotation_id = fields.Many2one("sale.order", string="Quotation")
