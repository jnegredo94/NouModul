from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime

class FacturesRoutesPartialDelivery(models.TransientModel):
    _name = "factures.delivery.routes.partial.delivery"
    _description = "Interface to select the quotations to mark as delivered or not"
    
    parent_id = fields.Many2one("factures.delivery.routes.generated", string="Parent", ondelete="cascade", default=lambda self: self.env.context.get("active_id"), readonly=True)
    #selected_quotations from the parent_id
    selected_quotations = fields.Many2many("sale.order", string="Quotations")
    
    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        self.selected_quotations = self.parent_id.quotation_ids
    
    def confirm_selection(self):
        
        #itarate over the parent_id.quotation_ids and if they are in the selected_quotations, mark them as delivered
        for quotation in self.parent_id.quotation_ids:
            if quotation in self.selected_quotations:
                quotation.write({"delivery_status": "full"})
