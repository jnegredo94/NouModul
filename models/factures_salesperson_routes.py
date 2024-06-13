from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class FacturesSalesPersonRoutes(models.Model):
    _name = "factures.salesperson.routes"
    _description = "Routes for salesperson"

    name = fields.Char("Name", required=True, help="Name of the route")
    code = fields.Char("Code", required=True, help="Code of the route")
    description = fields.Text("Description", help="Description of the route")
    active = fields.Boolean("Active", default=True, help="If the route is active or not")
    salesperson_id = fields.Many2one("res.users", "Salesperson", required=True, help="Salesperson for the route")

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
            partners = self.env["res.partner"].search([("salesperson_route_id.code", "=", self.code)])
            if len(partners) > 0:
                partners_message = "\n".join([partner.name for partner in partners[:10]])
                if len(partners) > 10:
                    partners_message += "\n..."
                raise UserError(
                    f"{len(partners)} partners are using this route:\n{partners_message}")
