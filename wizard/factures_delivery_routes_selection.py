from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime

class FacturesRoutesSelection(models.TransientModel):
    _name = "factures.delivery.routes.selection"
    _description = "Interface to select the quotations to group together"
    
    
    date = fields.Date("Delivery Date", required=True, default=fields.Date.today())
    route_id = fields.Many2one("factures.delivery.routes", string="Routes", required=True)
    
    selected_quotations = fields.Many2many("sale.order", string="Quotations")
    
    @api.onchange("date", "route_id")
    def _onchange_dates_and_route(self):
        if self.date and self.route_id:
            
            start_datetime = datetime.combine(self.date, datetime.min.time())
            end_datetime = datetime.combine(self.date, datetime.max.time())
            
            self.selected_quotations = self.env["sale.order"].search([
                ("commitment_date", ">=", start_datetime),
                ("commitment_date", "<=", end_datetime),
                ("state", "=", "sale"),
                ("partner_id.delivery_route_id", "=", self.route_id.id),
                ("delivery_status", "!=", "full")
            ])
        else:
            self.selected_quotations = False
        
    def group_quotations(self):
        # Get the selected quotations
        quotations = self.selected_quotations
        
        # Get all the active routes 
        routes = self.env["factures.delivery.routes"].search([])
        
        # Group the quotations by route and date
        quotations_by_route_date = {}
        for quotation in quotations.filtered(lambda q: q.partner_id.delivery_route_id):
            route_id = quotation.partner_id.delivery_route_id.id
            commitment_date = quotation.commitment_date.date()
            if (route_id, commitment_date) not in quotations_by_route_date:
                quotations_by_route_date[(route_id, commitment_date)] = []
            quotations_by_route_date[(route_id, commitment_date)].append(quotation.id)
            
        # Create or update the records
        for route in routes:
            for route_date, quotation_ids in quotations_by_route_date.items():
                route_id, commitment_date = route_date
                record = self.env["factures.delivery.routes.generated"].search([
                    ("route_id", "=", route_id),
                    ("date", "=", commitment_date)
                ])
                if not record:
                    self.env["factures.delivery.routes.generated"].create({
                        "route_id": route_id,
                        "date": commitment_date,
                        "quotation_ids": [(6, 0, quotation_ids)]
                    })
                else:
                    record.write({"quotation_ids": [(6, 0, quotation_ids)]})
        
        return {
            "name": "Quotations by Route",
            "type": "ir.actions.act_window",
            "res_model": "factures.delivery.routes.generated",
            "view_mode": "tree,form",
            "domain": [],
        }
