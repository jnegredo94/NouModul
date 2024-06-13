from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class FacturesDiscountsSearch(models.Model):
    _name = 'factures.discounts.search'
    _description = 'factures.discounts.search'
    
    partner_id = fields.Many2one("res.partner", "Partner", required=True, help="Partner to search discounts")
    
    pricelist_item_ids = fields.Many2many("product.pricelist.item", string="Pricelist Items", help="Pricelist items for this partner")
    
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for record in self:
            record.pricelist_item_ids = record.partner_id.property_product_pricelist.item_ids
    