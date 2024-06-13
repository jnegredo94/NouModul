from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime

class FacturesSalespersonRoutesSelection(models.TransientModel):
    _name = "factures.salesperson.routes.selection"
    _description = "Interface to select the quotations to group together"
    
    start_date = fields.Date("Start Date", required=True,default=lambda self: datetime.today().replace(day=1))
    end_date = fields.Date("End Date", required=True, default=fields.Date.today())
    salesperson_route_id = fields.Many2one("factures.salesperson.routes", "Route", required=True, help="Route for salesperson")
    selected_quotations = fields.Many2many("sale.order", string="Quotations")
    
    @api.onchange("start_date", "end_date", "salesperson_route_id")
    def _onchange_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise UserError("The start date must be before the end date")
            if self.start_date > datetime.today().date():
                raise UserError("The start date cannot be in the future")
            if self.end_date > datetime.today().date():
                raise UserError("The end date cannot be in the future")
            if self.salesperson_route_id:
                self.selected_quotations = self.env["sale.order"].search([
                    ("date_order", ">=", self.start_date),
                    ("date_order", "<=", self.end_date),
                    ("state", "=", "sale"),
                    ("partner_id.salesperson_route_id", "=", self.salesperson_route_id.id),
                ])
            else:
                self.selected_quotations = self.env["sale.order"].search([
                    ("date_order", ">=", self.start_date),
                    ("date_order", "<=", self.end_date),
                    ("state", "=", "sale"),
                ])
        else:
            self.selected_quotations = False
        
        
    
    def print_report(self):
        if not self.selected_quotations:
            raise UserError("No quotations selected")
        
        report = self.env.ref("factures.report_salesperson_routes_partner")
        return report.report_action(self)
        
        
    
    # create a dict with the format {(partner_id, partner_name): [(product_id,product_name, quantity)]}
    def group_by_partner(self):
        partner_product_quantities = {}

        for quotation in self.selected_quotations:
            for line in quotation.order_line:
                if line.product_id.name == "Discount":
                    continue
                partner_key = (quotation.partner_id.id,
                               quotation.partner_id.name)
                product_key = (line.product_id.id, line.product_id.name)
                quantity = line.product_uom_qty

                for index, (existing_product_id, existing_product_name, existing_quantity) in enumerate(partner_product_quantities.get(partner_key, [])):
                    if existing_product_id == product_key[0]:
                        partner_product_quantities[partner_key][index] = (
                            existing_product_id, existing_product_name, existing_quantity + quantity)
                        break
                else:
                    partner_product_quantities.setdefault(partner_key, []).append(
                        (product_key[0], product_key[1], quantity))

        return partner_product_quantities.items()    
        
