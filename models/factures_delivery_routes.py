from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class FacturesDeliveryRoutes(models.Model):
    _name = "factures.delivery.routes"
    _description = "Routes for delivery"

    name = fields.Char("Name", required=True, help="Name of the route")
    code = fields.Char("Code", required=True, help="Code of the route")
    description = fields.Text("Description", help="Description of the route")
    active = fields.Boolean("Active", default=True, help="If the route is active or not")

    _sql_constraints = [
        ("code_uniq", "unique(code)", "The code of the route must be unique"),
    ]

    @api.constrains("code")
    def _check_code(self):
        for route in self:
            if not route.code.isalnum():
                raise ValidationError("The code must be alphanumeric.")

    @api.constrains("active")
    def _onchange_active(self):
        if not self.active:
            partners = self.env["res.partner"].search([("delivery_route_id.code", "=", self.code)])
            if len(partners) > 0:
                partners_message = "\n".join([partner.name for partner in partners[:10]])
                if len(partners) > 10:
                    partners_message += "\n..."
                raise UserError(
                    f"{len(partners)} partners are using this route:\n{partners_message}")
