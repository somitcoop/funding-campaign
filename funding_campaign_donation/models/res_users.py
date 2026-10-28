# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Redefinir el campo para que apunte a funding.campaign en lugar de donation.campaign
    context_donation_campaign_id = fields.Many2one(
        'funding.campaign', 
        'Current Funding Campaign',
        help='Current funding campaign for donation context'
    )
    
    # Mantener la definición del payment mode (no cambia)
    context_donation_payment_mode_id = fields.Many2one(
        "account.payment.mode",
        "Current Donation Payment Mode",
        domain=[("donation", "=", True)],
        company_dependent=True,
    )
