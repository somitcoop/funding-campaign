# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    campaign_id = fields.Many2one(
        "funding.campaign",
        store=True,
        string="Campaign",
        tracking=True,
        help="Campaign associated with this subscription request",
    )

    skip_iban_control = fields.Boolean(
        string="Skip IBAN Control",
        help="Skip IBAN validation for automatic validation",
    )

    @api.model
    def create(self, vals):
        """Override create to ensure campaign subscriptions always use increase_remunerated type"""
        # If this subscription request has a campaign_id, force type to be increase_remunerated
        if vals.get('campaign_id'):
            _logger.info(f"Campaign subscription detected (campaign_id: {vals['campaign_id']}). "
                        f"Forcing type to 'increase_remunerated' (was: {vals.get('type')})")
            vals['type'] = 'increase_remunerated'
        
        return super().create(vals)

    def get_invoice_vals(self, partner):
        """Override to prevent campaign_id from being copied to account.move"""
        invoice_vals = super().get_invoice_vals(partner)
        # Explicitly set campaign_id to False to prevent copying funding.campaign ID
        # to account.move.campaign_id which expects utm.campaign ID
        invoice_vals['campaign_id'] = False
        return invoice_vals
