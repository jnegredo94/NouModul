from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict


class FacturesRoutesGenerated(models.Model):
    _name = "factures.delivery.routes.generated"
    _description = "Quotations grouped by delivery route and by day"

    
    route_id = fields.Many2one("factures.delivery.routes", "Route", help="Route for delivery", ondelete='cascade')
    quotation_ids = fields.Many2many("sale.order", string="Quotations")
    date = fields.Date("Date", default=lambda self: fields.Date.today())
    status = fields.Selection([
        ("en_cours", "En cours"),
        ("tancat", "Tancat"),
        ("cancelat", "Cancelat")
    ], string="Status", default="en_cours")
    active = fields.Boolean("Active", default=True)


    # {(product_id,product_name): [(partner_name, quantity), (partner_name, quantity)]}
    def group_by_product(self):
        product_quantities = defaultdict(list)

        for quotation in self.quotation_ids:
            for line in quotation.order_line:
                if line.product_id.name == "Discount":
                    continue
                product_key = (line.product_id.id, line.product_id.name)
                partner_name = quotation.partner_id.name
                quantity = line.product_uom_qty
                partner_quantity = (partner_name, quantity)
                for index, (existing_partner, existing_quantity) in enumerate(product_quantities[product_key]):
                    if existing_partner == partner_name:
                        product_quantities[product_key][index] = (
                            existing_partner, existing_quantity + quantity)
                        break
                    else:
                        product_quantities[product_key].append(partner_quantity)
        return product_quantities.items()

    # {(partner_id, partner_name): [(product_id,product_name, quantity)]}
    def group_by_partner(self):
        partner_product_quantities = {}

        for quotation in self.quotation_ids:
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

    def mark_as_delivered(self):
        #Set the delivery_status of the selected quotations to "full" and iterate over the picking_ids to set the state to "done"
        for quotation in self.quotation_ids:
            if quotation.delivery_status == "full":
                continue
            for picking in quotation.picking_ids:
                if picking.state != "done":
                    picking.action_assign()
                    picking.button_validate()
            quotation.delivery_status = "full"
        self.action_set_to_tancat()
        
    def partial_deliver(self):
        ###
        # Opens a wizard to select the quotations that have been delivered
        ###
        return {
            "name": "Partial Delivery",
            "type": "ir.actions.act_window",
            "res_model": "factures.delivery.routes.partial.delivery",
            "view_mode": "form",
            "target": "new",
            "parent_id": self.id,
            "context": {
                "quotations": self.quotation_ids.ids
            }
        }
        
    
    def action_set_to_tancat(self):
        #check if all the quotations are delivered
        for quotation in self.quotation_ids:
            if quotation.delivery_status != "full":
                raise UserError("Not all the quotations are delivered")
        self.status = "tancat"
        self.active = False
    def action_set_to_cancelat(self):
        #to be implemented
        raise ValidationError("Not implemented yet")
    def action_set_to_en_cours(self):
        self.status = "en_cours"
        self.active = True
        
    @api.onchange("status")
    def _onchange_status(self):
        if self.status == "tancat":
            self.active = False
        elif self.status == "cancelat":
            raise ValidationError("Not implemented yet")
        else:
            self.active = True