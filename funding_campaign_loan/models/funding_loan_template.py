from odoo import models, fields, api

class FundingLoanTemplate(models.Model):
    _name = 'funding.loan.template'
    _description = 'Loan Template'

    name = fields.Char('Name', required=True)
    loan_type = fields.Selection([
        ('fixed-annuity', 'Fixed Annuity'),
        ('fixed-annuity-begin', 'Fixed Annuity Begin'),
        ('fixed-principal', 'Fixed Principal'),
        ('interest', 'Only interest')
    ], required=True, default='interest')
    is_permanent = fields.Boolean('Is Permanent Loan', default=True)
    rate = fields.Float('Interest Rate (%)', required=True)
    min_amount = fields.Monetary('Minimum Amount', currency_field='company_currency_id')
    max_amount = fields.Monetary('Maximum Amount', currency_field='company_currency_id')
    min_periods = fields.Integer('Minimum Periods', default=60)
    method_period = fields.Integer('Period Length (months)', default=1)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id'
    )
    journal_id = fields.Many2one('account.journal', required=True)
    interest_expenses_account_id = fields.Many2one('account.account', required=True)
