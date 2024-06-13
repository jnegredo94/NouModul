from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    discount_invoice = fields.Float(
        string="Discount (%)", default=0.0, help="Discount for the invoice"
    )
    # discount_invoice_amount = fields.Monetary(
    #     string="Discount Amount",
    #     store=True,
    #     help="Discount amount for the invoice",
    # )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.discount_invoice = self.partner_id.discount_factura

    # def _ensure_discount_lines(self):
    #     self.ensure_one()
    #     self.write(
    #         {
    #             "line_ids": [
    #                 (2, line.id)
    #                 for line in self.line_ids
    #                 if line.product_id == self.company_id.sale_discount_product_id
    #             ]
    #         }
    #     )

    # def _add_discount_line(self):
    #     self.ensure_one()
    #     discount_product = self.company_id.sale_discount_product_id

    #     if not discount_product:
    #         raise UserError(_("No discount product found."))

    #     self.env["account.move.line"].create(
    #         {
    #             "move_id": self.id,
    #             "product_id": discount_product.id,
    #             "name": discount_product.name,
    #             "quantity": 1,
    #             "price_unit": -self.discount_invoice_amount,
    #             "tax_ids": [(6, 0, discount_product.taxes_id.ids)],
    #         }
    #     )

    # def _create_discount_lines(self):
    #     for record in self:
    #         if record.discount_invoice > 0:
    #             total = sum(line.price_subtotal for line in record.invoice_line_ids)
    #             record.discount_invoice_amount = total * record.discount_invoice
    #             record._ensure_discount_lines()
    #             record._add_discount_line()

    # @api.onchange("discount_invoice", "invoice_line_ids")
    # def _onchange_discount_invoice(self):
    #     self.ensure_one()
    #     for record in self:
    #         record._create_discount_lines()
