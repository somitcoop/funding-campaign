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

    def get_invoice_vals(self, partner):
        """Override to prevent campaign_id from being copied to account.move"""
        invoice_vals = super().get_invoice_vals(partner)
        # Explicitly set campaign_id to False to prevent copying funding.campaign ID
        # to account.move.campaign_id which expects utm.campaign ID
        invoice_vals['campaign_id'] = False
        return invoice_vals
