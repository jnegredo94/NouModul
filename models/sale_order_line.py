from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    display_discount = fields.Char(string="Discount", store=True, compute="_compute_discount_display")
    
    
    
    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        
        if not self.product_template_id:
            return
        if self.product_template_id.packaging_ids:
            
            self.product_packaging_id = self.product_template_id.packaging_ids[0]
            self.product_packaging_qty = 1.0
            self.product_uom_qty = self.product_template_id.packaging_ids[0].qty
    
    @api.constrains('discount')
    def _check_discount(self):
        for line in self:
            if line.discount > 100:
                raise ValidationError(_("Discount can't be greater than 100."))
            if line.discount < 0:
                raise ValidationError(_("Discount can't be negative."))
                
    
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_discount(self):
        for order_line in self:
            
            if not order_line.product_id or order_line.display_type:
                order_line.discount = 0.0
                
            discount_albara = order_line.order_id.discount_albara or 0
            
            if not (
                order_line.order_id.pricelist_id
                and order_line.order_id.pricelist_id.discount_policy == 'without_discount'
            ):
                order_line.discount = discount_albara*100
                continue

            order_line.discount = 0.0

            order_line = order_line.with_company(order_line.company_id)
            if order_line.pricelist_item_id:
                pricelist_price = order_line._get_pricelist_price()
                base_price = order_line._get_pricelist_price_before_discount()
            else:
                pricelist_price = order_line.price_unit
                base_price = order_line.price_unit
            
            if base_price != 0:
                discount = (base_price - pricelist_price) / base_price * 100
                
                if ((discount > 0 and base_price > 0) or (discount_albara > 0 and base_price > 0)) or (discount < 0 and base_price < 0): 
                    # only show negative discounts if price is negative
                    # otherwise it's a surcharge which shouldn't be shown to the customer
                    
                    subtotal = order_line.price_unit * order_line.product_uom_qty
                    final_price = subtotal * (1 - (discount / 100)) * (1 - discount_albara)
                    
                    total_percentage_decrease = ((subtotal - final_price) / subtotal) * 100
                    
                    order_line.discount = total_percentage_decrease
                    
                    if order_line.price_unit < 0:
                        order_line.discount = 0.0


    @api.depends('discount', 'display_discount')
    def _compute_discount_display(self):
        for order_line in self:
            discount_albara = order_line.order_id.discount_albara or 0
            
            if order_line.pricelist_item_id:
                pricelist_price = order_line._get_pricelist_price()
                base_price = order_line._get_pricelist_price_before_discount()
            else:
                pricelist_price = order_line.price_unit
                base_price = order_line.price_unit
            
            if base_price != 0:
                discount = (base_price - pricelist_price) / base_price * 100
            
                all_discounts = [discount, discount_albara*100]
                display_text = ""
                for d in all_discounts:
                    if d == 0 or order_line.price_unit < 0:
                        continue
                    display_text += str(round(d,2)) + "+"
                display_text = display_text[:-1]
                order_line.display_discount = display_text
                
            
    