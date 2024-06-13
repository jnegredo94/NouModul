from odoo import _,api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class FacturesInvoiceConfirmation(models.TransientModel):
    _name = "factures.invoice.confirmation"
    _description = "Factures Invoice Confirmation"

    start_date = fields.Date("Start date", required=True)
    end_date = fields.Date("End date", required=True)
    temp_invoice_id = fields.Many2many("factures.invoice.temp", string="Temp Invoice")
    selected_quotations = fields.Many2many("sale.order", string="Sales")
    invoice_ids = fields.Many2many("account.move", string="Invoices")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.onchange("start_date", "end_date")
    def set_invoices(self):
        temp_dict = {}
        for sale in self.selected_quotations:
            partner_id = sale.partner_id.id
            payment_method_id = sale.payment_method.id if sale.payment_method else False
            key = (partner_id, payment_method_id)
            temp_dict.setdefault(key, []).append(sale.amount_total)

        temp_invoice_ids_list = []
        for (partner_id, payment_method_id), amounts in temp_dict.items():
            total_amount = sum(amounts)
            temp_invoice = self.env["factures.invoice.temp"].create(
                {
                    "partner_id": partner_id,
                    "payment_method_id": payment_method_id,
                    "total_amount": total_amount,
                    "invoice_quotations": [
                        (6, 0, self.selected_quotations.filtered(
                            lambda x: x.partner_id.id == partner_id
                            and (
                                not payment_method_id
                                or x.payment_method.id == payment_method_id
                            )
                        ).ids)
                    ],
                }
            )
            temp_invoice_ids_list.append(temp_invoice.id)
        self.temp_invoice_id = self.env["factures.invoice.temp"].search(
            [("id", "in", temp_invoice_ids_list)]
        )
        
    def _prepare_discount_product_values(self):
        self.ensure_one()
        return {
            "name": _("Discount"),
            "type": "service",
            "invoice_policy": "order",
            "list_price": 0.0,
            "company_id": self.company_id.id,
            "taxes_id": None,
        }

    def confirm_invoices(self):
        invoices = {}
        for sale in self.selected_quotations:
            partner_id = sale.partner_id.id
            partner_invoice_id = sale.partner_invoice_id.id  # Get partner invoice id
            partner_shipping_id = sale.partner_shipping_id.id  # Get partner shipping id
            payment_method_id = sale.payment_method.id if sale.payment_method else False
            key = (partner_id, partner_invoice_id, partner_shipping_id, payment_method_id)
            invoices.setdefault(key, []).append(sale)

        for (partner_id, partner_invoice_id, partner_shipping_id, payment_method_id), partner_quotations in invoices.items():
            invoice_lines = []

            for quotation in partner_quotations:
                invoice_lines.append(
                    (0, 0, {
                        "name": f"Quotation {quotation.name}",
                        "price_unit": quotation.amount_total,
                        "quotation_id": quotation.id,
                    })
                )

            # Add discount product line
            discount_product = self.company_id.sale_discount_product_id
            if not discount_product:
                self.company_id.sale_discount_product_id = self.env["product.product"].create(self._prepare_discount_product_values())
                discount_product = self.company_id.sale_discount_product_id
            total_amount = sum(quotation.amount_total for quotation in partner_quotations)
            discount_amount = total_amount * self.env["res.partner"].browse(partner_id).discount_factura
            if discount_amount > 0:
                invoice_lines.append(
                    (0, 0, {
                        "product_id": discount_product.id,
                        "name": discount_product.name,
                        "quantity": 1,
                        "price_unit": -discount_amount,
                    })
                )

            payment_day = self.env["res.partner"].browse(partner_id).day_of_payment
            date = fields.Date.today().replace(day=payment_day, month=fields.Date.today().month + 1)

            invoice = self.env["account.move"].create(
                {
                    "partner_id": partner_invoice_id if partner_invoice_id else partner_id,  # Set partner_invoice_id if available
                    "partner_shipping_id": partner_shipping_id if partner_shipping_id else partner_id,  # Set partner_shipping_id if available
                    "move_type": "out_invoice",
                    "invoice_date": fields.Date.today(),
                    "invoice_line_ids": invoice_lines,
                    "invoice_date_due": date,
                    "discount_invoice": quotation.partner_id.discount_factura,  # Applying discount to invoice
                }
            )
            invoice.action_post()

            # payment_method_line_id = self.env["account.payment.method.line"].search(
            #     [("payment_method_id", "=", payment_method_id)], limit=1
            # )
            
            # #journal_id  from the sdd.mandate model for the partner_id
            # journal_id = self.env["sdd.mandate"].search([("partner_id", "=", partner_id)], limit=1).payment_journal_id.id
            
            
            # register_payment = self.env["account.payment.register"].create(
            #     {
            #         "payment_date": fields.Date.today(),
            #         "payment_method_id": payment_method_id,
            #         "journal_id": payment_method_line_id.journal_id.id,
            #         "payment_difference_handling": "open",
            #         "amount": invoice.amount_total,
            #         "currency_id": invoice.currency_id.id,
            #         "payment_type": "inbound",
            #         "partner_id": partner_id,
            #         "communication": invoice.name,
            #         "journal_id": journal_id,
            #     }
            # )
                        
            # register_payment.action_create_payments()
            

            # payment = self.env["account.payment"].create(
            #     {
            #         "payment_type": "inbound",
            #         "partner_type": "customer",
            #         "partner_id": partner_id,
            #         "amount": invoice.amount_total,
            #         "currency_id": invoice.currency_id.id,
            #         "payment_reference": invoice.name,
            #         "payment_method_id": payment_method_id,
            #         "payment_method_line_id": payment_method_line_id.id,
            #         "ref": invoice.name,
            #     }
            # )
            # invoice.payment_id = payment
            # payment.action_post()
            # invoice.payment_state = "paid"
            

            for quotation in partner_quotations:
                quotation.invoice_status = "invoiced"
                quotation.invoice_ids = [(4, invoice.id)]# If you want to add the invoice to the sale order you have to override the compute method of the invoice_ids field in the sale.order model (_get_invoiced)
                quotation.invoice_count = len(invoices)# same as above

        self.invoice_ids = self.env["account.move"].search(
            [("id", "in", self.mapped("selected_quotations").mapped("id"))]
        )

