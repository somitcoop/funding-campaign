# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingCampaign(models.Model):
    _name = "funding.campaign"
    _description = "Funding Campaign"

    name = fields.Char("Name", required=True)
    start_date = fields.Date("Start Date", required=True)
    end_date = fields.Date("End Date")
    is_permanent = fields.Boolean("Permanent", default=False)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
    )
    global_objective = fields.Float("Global Objective")
    funding_source_ids = fields.Many2many("funding.source", string="Funding Sources")
    marketing_campaign_id = fields.Many2one(
        "mailing.mailing", string="Marketing Campaign", ondelete="set null"
    )
    progress = fields.Float("Progress (%)", compute="_compute_progress", store=True)

    @api.depends("funding_source_ids.progress", "global_objective")
    def _compute_progress(self):
        for campaign in self:
            total_raised = sum(
                source.raised_amount for source in campaign.funding_source_ids
            )
            if campaign.global_objective:
                campaign.progress = (total_raised / campaign.global_objective) * 100
            else:
                campaign.progress = 0.0

    def action_start_campaign(self):
        for campaign in self:
            if campaign.state != "draft":
                raise UserError(_("Only campaigns in Draft status can be opened."))
            if not campaign.start_date:
                raise ValidationError(
                    _("Start Date is mandatory to start the campaign.")
                )
            campaign.state = "open"

    def action_finalize_campaign(self):
        for campaign in self:
            if campaign.state != "open":
                raise UserError(_("Only campaigns in Open status can be closed."))
            campaign.state = "closed"
