# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DonationCampaign(models.Model):
    _inherit = 'donation.campaign'

    funding_campaign_id = fields.Many2one(
        'funding.campaign',
        string='Funding Campaign',
        help='Related funding campaign that replaces this donation campaign'
    )

    def action_open_funding_campaign(self):
        self.ensure_one()
        if not self.funding_campaign_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'funding.campaign',
            'res_id': self.funding_campaign_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
