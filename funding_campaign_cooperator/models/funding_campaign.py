# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingCampaign(models.Model):
    _inherit = 'funding.campaign'

    has_subscription_source = fields.Boolean(
        string='Has Subscription Source',
        compute='_compute_has_subscription_source',
        store=True,
    )

    subscription_request_ids = fields.One2many(
        'subscription.request',
        'campaign_id',
        string='Subscription Requests',
    )

    source_raised_amount = fields.Monetary(
        string='Source Raised Amount',
        compute='_compute_source_raised_amount',
        currency_field='company_currency_id',
        store=True
    )

    @api.depends('funding_source_ids.raised_amount')
    def _compute_source_raised_amount(self):
        for campaign in self:
            campaign.source_raised_amount = sum(
                source.raised_amount
                for source in campaign.funding_source_ids
            )

    @api.depends('funding_source_ids.source_type')
    def _compute_has_subscription_source(self):
        for campaign in self:
            campaign.has_subscription_source = any(
                source.source_type == 'subscription'
                for source in campaign.funding_source_ids
            )

    def action_view_subscription_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscription Requests',
            'res_model': 'subscription.request',
            'view_mode': 'tree,form',
            'domain': [('campaign_id', '=', self.id)],
            'context': {'default_campaign_id': self.id},
        }
