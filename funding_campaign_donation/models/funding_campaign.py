# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingCampaign(models.Model):
    _inherit = 'funding.campaign'

    has_donation_source = fields.Boolean(
        string="Has Donation Source",
        compute="_compute_has_donation_source",
        store=True,
    )

    donation_ids = fields.One2many(
        "donation.donation",
        "campaign_id",
        string="Donations",
    )

    donation_raised_amount = fields.Monetary(
        string="Donation Raised Amount",
        compute="_compute_donation_raised_amount",
        currency_field="company_currency_id",
        store=True,
    )

    source_objective_donation = fields.Float(
        string="Donation Objective Amount",
        store=True
    )

    progress_donation = fields.Float(
        "Progress",
        compute="_compute_progress_donation",
        store=True,
        group_operator="avg",
    )

    donation_count = fields.Integer(
        string="Number of Donations",
        compute="_compute_donation_count",
        store=True,
    )

    minimal_donation_amount = fields.Float(
        string="Minimal Donation Amount",
        store=True,
    )

    @api.depends("donation_raised_amount", "source_objective_donation")
    def _compute_progress_donation(self):
        for campaign in self:
            if campaign.source_objective_donation:
                campaign.progress_donation = (
                    campaign.donation_raised_amount / campaign.source_objective_donation
                ) * 100
            else:
                campaign.progress_donation = 0.0

    @api.depends("funding_source_ids", "funding_source_ids.source_type")
    def _compute_has_donation_source(self):
        for campaign in self:
            campaign.has_donation_source = any(
                source.source_type == "donation" for source in campaign.funding_source_ids
            )

    @api.depends(
        "donation_ids",
        "donation_ids.amount_total",
        "donation_ids.state"
    )
    def _compute_donation_raised_amount(self):
        for campaign in self:
            campaign.donation_raised_amount = sum(
                donation.amount_total
                for donation in campaign.donation_ids
                if donation.state == "done"
            )

    @api.depends("donation_ids")
    def _compute_donation_count(self):
        for campaign in self:
            campaign.donation_count = len(campaign.donation_ids)

    def action_view_donations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Donations",
            "res_model": "donation.donation",
            "view_mode": "tree,form",
            "domain": [("campaign_id", "=", self.id)],
            "context": {"default_campaign_id": self.id},
        }

    @api.depends("source_objective_donation")
    def _compute_global_objective(self):
        return super()._compute_global_objective()

    def _get_objective_amounts(self):
        amounts = super()._get_objective_amounts()
        if hasattr(self, "source_objective_donation"):
            amounts.append(self.source_objective_donation or 0.0)
        return amounts

    def _get_raised_amounts(self):
        amounts = super()._get_raised_amounts()
        if hasattr(self, "donation_raised_amount"):
            amounts.append(self.donation_raised_amount or 0.0)
        return amounts

    @api.depends(
        "funding_source_ids",
        "funding_source_ids.progress",
        "global_objective",
        "donation_raised_amount",
    )
    def _compute_progress(self):
        return super()._compute_progress()
