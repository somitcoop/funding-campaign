# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingCampaign(models.Model):
    _inherit = "funding.campaign"

    has_loan_source = fields.Boolean(
        string="Has Loan Source", compute="_compute_has_loan_source", store=True
    )

    loan_request_ids = fields.One2many(
        "funding.loan.request", "campaign_id", string="Loan Requests"
    )

    loan_raised_amount = fields.Monetary(
        string="Loan Raised Amount",
        compute="_compute_loan_raised_amount",
        currency_field="company_currency_id",
        store=True,
    )
    progress_loan = fields.Float(
        "Progress", compute="_compute_progress_loan", store=True, group_operator="avg"
    )

    loan_request_count = fields.Integer(
        string="Number of Loan Requests",
        compute="_compute_loan_request_count",
        store=True,
    )

    @api.depends("loan_raised_amount", "source_objective_loan")
    def _compute_progress_loan(self):
        for campaign in self:
            if campaign.source_objective_loan:
                campaign.progress_loan = (
                    campaign.loan_raised_amount / campaign.source_objective_loan
                ) * 100
            else:
                campaign.progress_loan = 0.0

    template_id = fields.Many2one(
        "funding.loan.template",
    )

    source_objective_loan = fields.Float(string="Loan Objective Amount", store=True)

    @api.depends("funding_source_ids", "funding_source_ids.source_type")
    def _compute_has_loan_source(self):
        for campaign in self:
            campaign.has_loan_source = any(
                source.source_type == "loan" for source in campaign.funding_source_ids
            )

    @api.depends(
        "loan_request_ids", "loan_request_ids.loan_amount", "loan_request_ids.state"
    )
    def _compute_loan_raised_amount(self):
        for campaign in self:
            campaign.loan_raised_amount = sum(
                request.loan_amount
                for request in campaign.loan_request_ids
                if request.state == "approved"
            )

    @api.depends("loan_request_ids")
    def _compute_loan_request_count(self):
        for campaign in self:
            campaign.loan_request_count = len(campaign.loan_request_ids)

    def action_view_loan_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Loan Requests",
            "res_model": "funding.loan.request",
            "view_mode": "tree,form",
            "domain": [("campaign_id", "=", self.id)],
            "context": {"default_campaign_id": self.id},
        }

    @api.depends("source_objective_loan")
    def _compute_global_objective(self):
        return super()._compute_global_objective()

    def _get_objective_amounts(self):
        amounts = super()._get_objective_amounts()
        if hasattr(self, "source_objective_loan"):
            amounts.append(self.source_objective_loan or 0.0)
        return amounts

    @api.depends("funding_source_ids", "global_objective")
    def _get_raised_amounts(self):
        amounts = super()._get_raised_amounts()
        if hasattr(self, "loan_raised_amount"):
            amounts.append(self.loan_raised_amount or 0.0)
        return amounts

    @api.depends(
        "funding_source_ids",
        "funding_source_ids.progress",
        "global_objective",
        "loan_raised_amount",
    )
    def _compute_progress(self):
        return super()._compute_progress()
