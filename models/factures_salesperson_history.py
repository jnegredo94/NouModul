from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

from odoo import api, fields, models

from odoo import api, fields, models

class FacturesSalespersonHistoryLine(models.Model):
    _name = 'factures.salesperson.history.line'
    _description = 'factures.salesperson.history.line'

    factures_salesperson_history_id = fields.Many2one('factures.salesperson.history', string='FacturesSalespersonHistory')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Unitats',  readonly=False, help='Number of units', compute='_compute_product_qty', inverse='_inverse_product_qty')
    product_packaging_qty = fields.Float(string='Caixes', default=1, readonly=False, help='Number of boxes')
    qty_packaging = fields.Float(string='Unitats / Caixa', store=True, default=1, inverse='_inverse_qty_packaging')
    product_packaging = fields.Many2one('product.packaging', string='Tipus de caixa', domain="[('product_id', '=', product_id)]", store=True, readonly=False)

    @api.depends('product_packaging_qty', 'qty_packaging')
    def _compute_product_qty(self):
        for record in self:
            record.product_qty = record.product_packaging_qty * record.qty_packaging

    def _inverse_product_qty(self):
        for record in self:
            if record.qty_packaging != 0:
                record.product_packaging_qty = record.product_qty / record.qty_packaging
            else:
                record.product_packaging_qty = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and record.product_id.packaging_ids:
                record.product_packaging = record.product_id.packaging_ids[0].id or False
            else:
                record.product_packaging = False

    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        for record in self:
            if record.product_packaging:
                record.qty_packaging = record.product_packaging.qty
            else:
                record.qty_packaging = 1

    def _inverse_qty_packaging(self):
        for record in self:
            if record.qty_packaging:
                product_packaging = self.env['product.packaging'].search([('product_id', '=', record.product_id.id), ('qty', '=', record.qty_packaging)], limit=1)
                if product_packaging:
                    record.product_packaging = product_packaging.id

   
        
        
    
class FacturesSalespersonHistory(models.Model):
    """
    Model for the history of the partner 
    """
    _name = 'factures.salesperson.history'
    _description  = 'factures.salesperson.history'
    
    _sql_constraints = [
        ('unique_partner_route_date', 'UNIQUE(partner_id, salesperson_route_id, date)', _('Partner, Route, and Date must be unique!'))
    ]
    
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    salesperson_route_id = fields.Many2one('factures.salesperson.routes', string='Route', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today())
    factures_salesperson_history_lines = fields.One2many('factures.salesperson.history.line', 'factures_salesperson_history_id', string='Lines', ondelete='cascade')
    
    
    
    