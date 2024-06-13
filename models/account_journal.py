from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    ref_bank = fields.Many2one(
        'account.journal',
        string='Bank Reference',
        domain="[('type', '=', 'bank')]",
        help="Bank account used as reference for SEPA Direct Debit payments.",
        readonly=False,        
    )
    
    
    
            
