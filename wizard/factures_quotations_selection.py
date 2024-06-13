from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class FacturesQuotationsSelection(models.TransientModel):
    _name = "factures.quotations.selection"
    _description = "Interface to select the quotations to invoice together"

    start_date = fields.Date("Start date", default=lambda self: datetime.today().replace(day=1))
    end_date = fields.Date("End date", default=fields.Date.today())

    total_days = fields.Integer("Number of days selected", compute="_compute_total_days")
    selected_quotations = fields.Many2many("sale.order", string="Sales")

    @api.depends("start_date", "end_date")
    def _compute_total_days(self):
        for record in self:
            if record.start_date and record.end_date:
                record.total_days = (record.end_date - record.start_date).days

    @api.onchange("start_date", "end_date")
    def _on_change_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise UserError("The start date must be before the end date")
            self.selected_quotations = self.env["sale.order"].search([
                ("date_order", ">=", self.start_date),
                ("date_order", "<=", self.end_date),
                ("state", "=", "sale"),
            ])  # ("invoice_status", "=", "to invoice")
        else:
            self.selected_quotations = False

    def confirm_selection(self):
        if not self.selected_quotations:
            raise UserError("Please select at least one quotation to confirm")
        return {
            "name": "Confirm Invoice Creation",
            "type": "ir.actions.act_window",
            "res_model": "factures.invoice.confirmation",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_start_date": self.start_date,
                "default_end_date": self.end_date,
                "default_selected_quotations": self.selected_quotations.ids,
            },
        }
