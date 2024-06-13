from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FacturesPaymentGeneration(models.TransientModel):
    _name = 'factures.payment.generation'
    _description = 'Factures Payment Generation'

    due_date = fields.Date('Due Date', required=True)
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', string='Payment Method Line', required=True, default=lambda self: self.env['account.payment.method.line'].search([('payment_method_id.code', '=', 'sdd')], limit=1))  # sepa direct debit

    @api.onchange('due_date', 'invoice_ids')
    def _onchange_due_date_invoice_ids(self):
        if self.due_date:
            search_domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid'),
                ('payment_state', '!=', 'in_payment'),
                ('invoice_date_due', '<=', self.due_date)
            ]
            self.invoice_ids = self.env['account.move'].search(search_domain)
        else:
            self.invoice_ids = False

    def confirm_payment_generation(self):
        if not self.due_date:
            raise ValidationError(_('Please enter a due date.'))
        if not self.invoice_ids:
            raise ValidationError(_('Please select at least one invoice.'))
        if not self.payment_method_line_id:
            raise ValidationError(_('Please select a payment method line.'))

        # Group invoices by partner's payment journals
        partner_journals = {}
        for invoice in self.invoice_ids:
            mandate = self.env['sdd.mandate'].search(
                [('partner_id', '=', invoice.partner_id.id)], limit=1, order='start_date desc')
            if not mandate:
                raise ValidationError(
                    _('No SEPA Direct Debit mandate found for partner %s.') % invoice.partner_id.name)
            journal_used = mandate.payment_journal_id.ref_bank or mandate.payment_journal_id
            partner_journals.setdefault(journal_used, []).append(invoice)

        # Create payments
        payments = []
        for journal, invoices in partner_journals.items():
            for invoice in invoices:
                payment = self.env['account.payment'].create({
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": invoice.partner_id.id,
                    "payment_method_line_id": self.payment_method_line_id.id,
                    "amount": invoice.amount_total,
                    "currency_id": invoice.currency_id.id,
                    "payment_reference": invoice.name,
                    "ref": invoice.name,
                    "journal_id": journal.id,
                    "date": self.due_date,
                })

                payment.action_post()
                payments.append(payment)

                # Collect journal items (lines) for reconciliation
                journal_items = invoice.line_ids.filtered(
                    lambda line: line.account_id.reconcile and not line.reconciled)

                # Reconcile journal items
                domain = [
                    ('parent_state', '=', 'posted'),
                    ('account_type', 'in', payment._get_valid_payment_account_types()),
                    ('reconciled', '=', False),
                ]
                payment_lines = payment.line_ids.filtered_domain(domain)

                for account in payment_lines.mapped('account_id'):
                    (payment_lines + journal_items).filtered_domain([
                        ('account_id', '=', account.id),
                        ('reconciled', '=', False)
                    ]).reconcile()

        # Create batch payments for bank journals
        bank_journals = [
            journal for journal in partner_journals.keys() if journal.type == 'bank'
            ]
        for journal in bank_journals:
            payment_ids = [
                payment.id for payment in payments if payment.journal_id == journal
                ]

            batch_payment = self.env['account.batch.payment'].create({
                'journal_id': journal.id,
                'payment_ids': [(6, 0, payment_ids)],
                'batch_type': 'inbound',
            })

            # batch_payment.validate_batch()

        return {
            'name': _('Batch Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.batch.payment',
            'view_mode': 'tree,form',
        }
