# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingLoanRegister(models.Model):
    _name = 'funding.loan.register'
    _description = 'Loan Register'

    name = fields.Char(required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', required=True)
    loan_request_id = fields.Many2one('funding.loan.request', required=True)
    loan_id = fields.Many2one('account.loan', required=True)
    date = fields.Date(required=True)
    amount = fields.Monetary(currency_field='company_currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id'
    )
