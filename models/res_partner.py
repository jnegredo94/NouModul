from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    day_of_payment = fields.Integer("Day of Payment", required=True, default=1, help="Day of the month when the payment is due")
    
    discount_albara = fields.Float("Discount for Albara", required=True, default=0, help="Discount for Albara (between 0 and 100)")
    discount_factura = fields.Float("Discount for Factura", required=True, default=0, help="Discount for Factura (between 0 and 100)")
    discount_rappel = fields.Float("Discount for Rappel", required=True, default=0, help="Discount for Rappel (between 0 and 100)")
    
    delivery_route_id = fields.Many2one("factures.delivery.routes", "Delivery Route", help="Route for delivery")
    salesperson_route_id = fields.Many2one("factures.salesperson.routes", "Salesperson Route", help="Route for salesperson")
    
    pricelist_item_ids = fields.Many2many("product.pricelist.item", string="Pricelist Items", help="Pricelist items for this partner")
    
    @api.onchange("property_product_pricelist")
    def _onchange_property_product_pricelist(self):
        for record in self:
            record.pricelist_item_ids = record.property_product_pricelist.item_ids
    
    @api.constrains("discount_albara", "discount_factura", "discount_rappel")
    def _check_discount(self):
        for record in self:
            if not 0 <= record.discount_albara <= 1:
                raise ValidationError("Discount for Albara must be between 0 and 100.")
            if not 0 <= record.discount_factura <= 1:
                raise ValidationError("Discount for Factura must be between 0 and 100.")
            if not 0 <= record.discount_rappel <= 1:
                raise ValidationError("Discount for Rappel must be between 0 and 100.")
    
    @api.constrains("day_of_payment")
    def _check_day_of_payment(self):
        for record in self:
            if not 1 <= record.day_of_payment <= 31:
                raise ValidationError("Day of payment must be between 1 and 31.")
