from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_method = fields.Many2one("account.payment.method", string="Payment Method")
    discount_albara = fields.Float(string="Discount (%)")
    

    @api.constrains("discount_albara")
    def _check_discount(self):
        for record in self:
            if not 0 <= record.discount_albara <= 100:
                raise ValidationError(_("The discount must be between 0 and 100."))

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.discount_albara = self.partner_id.discount_albara

    @api.onchange("discount_albara")
    def _onchange_discount_albara(self):
        self.ensure_one()
        self._check_discount()

        for line in self.order_line:
            line._compute_discount()

