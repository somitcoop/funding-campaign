# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingCampaign(models.Model):
    _inherit = "funding.campaign"

    has_subscription_source = fields.Boolean(
        string="Has Subscription Source",
        compute="_compute_has_subscription_source",
        store=True,
    )

    subscription_request_ids = fields.One2many(
        "subscription.request",
        "campaign_id",
        string="Subscription Requests",
    )

    source_raised_amount = fields.Monetary(
        string="Source Raised Amount",
        compute="_compute_source_raised_amount",
        currency_field="company_currency_id",
        store=True,
    )

    share_product_id = fields.Many2one(
        "product.product",
        string="Share type",
        domain="[('is_share', '=', True)]",
    )

    source_objective_subscription = fields.Float(
        string="Subscription Objective Amount", store=True
    )

    progress_subscription = fields.Float(
        "Progress",
        compute="_compute_progress_subscription",
        store=True,
        group_operator="avg",
    )

    subscription_request_count = fields.Integer(
        string="Number of Subscription Requests",
        compute="_compute_subscription_request_count",
        store=True,
    )

    minimal_subscription_amount = fields.Float(
        string="Minimal Subscription Amount",
        store=True,
    )

    maximal_subscription_amount = fields.Float(
        string="Maximal Subscription Amount",
        store=True,
    )

    @api.depends("source_raised_amount", "source_objective_subscription")
    def _compute_progress_subscription(self):
        for campaign in self:
            if campaign.source_objective_subscription:
                campaign.progress_subscription = (
                    campaign.source_raised_amount
                    / campaign.source_objective_subscription
                ) * 100
            else:
                campaign.progress_subscription = 0.0

    @api.depends(
        "subscription_request_ids",
        "subscription_request_ids.state",
        "subscription_request_ids.subscription_amount",
    )
    def _compute_source_raised_amount(self):
        for campaign in self:
            campaign.source_raised_amount = sum(
                request.subscription_amount
                for request in campaign.subscription_request_ids
                if request.state == "done"
            )

    @api.depends("funding_source_ids.source_type")
    def _compute_has_subscription_source(self):
        for campaign in self:
            campaign.has_subscription_source = any(
                source.source_type == "subscription"
                for source in campaign.funding_source_ids
            )

    @api.depends("subscription_request_ids")
    def _compute_subscription_request_count(self):
        for campaign in self:
            campaign.subscription_request_count = len(campaign.subscription_request_ids)

    def action_view_subscription_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Subscription Requests",
            "res_model": "subscription.request",
            "view_mode": "tree,form",
            "domain": [("campaign_id", "=", self.id)],
            "context": {"default_campaign_id": self.id},
        }

    @api.depends("source_objective_subscription")
    def _compute_global_objective(self):
        return super()._compute_global_objective()

    def _get_objective_amounts(self):
        amounts = super()._get_objective_amounts()
        if hasattr(self, "source_objective_subscription"):
            amounts.append(self.source_objective_subscription or 0.0)
        return amounts

    def _get_raised_amounts(self):
        amounts = super()._get_raised_amounts()
        if hasattr(self, "source_raised_amount"):
            amounts.append(self.source_raised_amount or 0.0)
        return amounts

    @api.depends(
        "funding_source_ids",
        "funding_source_ids.progress",
        "global_objective",
        "source_raised_amount",
    )
    def _compute_progress(self):
        return super()._compute_progress()

    # === Contributions vinculadas ===
    contribution_ids = fields.One2many(
        "carsharing.contribution",
        "campaign_id",
        string="Contributions",
        help="Aportacions creades a partir de les subscripcions d'aquesta campanya. Es generen automàticament en validar i pagar les subscripcions.",
    )

    contribution_count = fields.Integer(
        string="Number of Contributions",
        compute="_compute_contribution_count",
        store=True,
        help="Nombre total d'aportacions generades per aquesta campanya.",
    )

    @api.depends("contribution_ids")
    def _compute_contribution_count(self):
        for campaign in self:
            campaign.contribution_count = len(campaign.contribution_ids)

    def action_view_contributions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Contributions",
            "res_model": "carsharing.contribution",
            "view_mode": "tree,form",
            "domain": [("campaign_id", "=", self.id)],
            "context": {"default_campaign_id": self.id},
        }

    # === Campos de templates por campaña ===
    contribution_contract_report_id = fields.Many2one(
        "ir.actions.report",
        string="Contribution Contract Report",
        domain="[('model', '=', 'carsharing.contribution')]",
        help="Plantilla QWeb (report) utilitzada per generar els contractes d'aportació d'aquesta campanya. Si no s'indica, s'usa el contracte per defecte.",
    )
    contribution_sign_template_id = fields.Many2one(
        "sign.oca.template",
        string="Signature Template",
        help="Plantilla de sign_oca utilitzada per a la signatura digital dels contractes d'aportació d'aquesta campanya.",
    )
    contribution_email_template_id = fields.Many2one(
        "mail.template",
        string="Contribution Email Template",
        domain="[('model_id.model', '=', 'carsharing.contribution')]",
        help="Plantilla de correu per enviar els contractes d'aportació als socis/es d'aquesta campanya.",
    )
