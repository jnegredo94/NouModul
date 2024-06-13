from odoo import api, fields, models
from odoo.exceptions import ValidationError

class FacturesInvoiceTemp(models.TransientModel):
    _name = "factures.invoice.temp"
    _description = "Temporary Invoice Model for Factures"
    _order = "partner_id"
    
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    total_amount = fields.Float("Total Amount", required=True)
    invoice_quotations = fields.Many2many("sale.order", string="Quotations")
    payment_method_id = fields.Many2one("account.payment.method", string="Payment Method", compute="_compute_payment_method")

    @api.depends("invoice_quotations")
    def _compute_payment_method(self):
        for invoice_temp in self:
            # Ensure all selected quotations have the same payment method
            payment_methods = invoice_temp.invoice_quotations.mapped("payment_method")
            if len(payment_methods) > 1:
                raise ValidationError("All quotations must have the same payment method")
            invoice_temp.payment_method_id = payment_methods[0] if payment_methods else False
