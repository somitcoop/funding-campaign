# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingSource(models.Model):
    _inherit = 'funding.source'

    source_type = fields.Selection(
        selection_add=[("donation", "Donations")],
        ondelete={"donation": "set default"}
    )

    @api.depends(
        "campaign_ids",
        "campaign_ids.donation_ids.amount_total",
        "campaign_ids.donation_ids.state",
    )
    def _compute_raised_amount(self):
        super()._compute_raised_amount()
        for source in self:
            if source.source_type == "donation":
                source.raised_amount = sum(
                    donation.amount_total
                    for campaign in source.campaign_ids
                    for donation in campaign.donation_ids
                    if donation.state == "done"
                )
