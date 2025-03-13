# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DonationDonation(models.Model):
    _inherit = 'donation.donation'

    def _remove_original_campaign_field(self):
        if hasattr(super(), 'campaign_id'):
            del self.campaign_id

    campaign_id = fields.Many2one(
        comodel_name='funding.campaign',
        string='Funding Campaign',
        tracking=True,
        check_company=True,
        ondelete='restrict',
        help='Associated funding campaign',
        default=lambda self: self.env.user.context_donation_campaign_id,
    )
