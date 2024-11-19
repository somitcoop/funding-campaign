# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingLoanRequest(models.Model):
    _name = 'funding.loan.request'
    _description = 'Loan Request'

    name = fields.Char(required=True, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', required=True)
    campaign_id = fields.Many2one('funding.campaign')
    template_id = fields.Many2one('funding.loan.template', required=True)
    loan_amount = fields.Monetary(currency_field='company_currency_id', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id'
    )
    loan_id = fields.Many2one('account.loan', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('funding.loan.request')
        return super().create(vals)

    def action_approve(self):
        self.ensure_one()
        # Crear préstamo
        loan_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id,
            'loan_type': self.template_id.loan_type,
            'is_permanent': self.template_id.is_permanent,
            'rate': self.template_id.rate,
            'loan_amount': self.loan_amount,
            'min_periods': self.template_id.min_periods,
            'method_period': self.template_id.method_period,
            'journal_id': self.template_id.journal_id.id,
            'interest_expenses_account_id': self.template_id.interest_expenses_account_id.id,
            'company_id': self.company_id.id
        }
        loan = self.env['account.loan'].create(loan_vals)
        self.write({
            'state': 'approved',
            'loan_id': loan.id
        })
