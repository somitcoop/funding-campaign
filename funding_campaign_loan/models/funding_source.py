# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FundingSource(models.Model):
    _inherit = 'funding.source'

    source_type = fields.Selection(
        selection_add=[('loan', 'Loan Requests')],
        ondelete={'loan': 'set default'}
    )

    loan_request_ids = fields.One2many(
        'funding.loan.request',
        'campaign_id',
        string='Loan Requests'
    )

    @api.depends('campaign_ids.loan_request_ids.loan_amount')
    def _compute_raised_amount(self):
        super()._compute_raised_amount()
        for source in self:
            if source.source_type == 'loan':
                source.raised_amount = sum(
                    request.loan_amount
                    for campaign in source.campaign_ids
                    for request in campaign.loan_request_ids
                    if request.state == 'approved'
                )

