# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingCampaign(models.Model):
    _name = "funding.campaign"
    _description = "Funding Campaign"
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
    global_objective = fields.Float(
        string="Global Objective Amount",
        compute="_compute_global_objective",
        store=True,
    )

    @api.depends()
    def _compute_global_objective(self):
        for campaign in self:
            campaign.global_objective = sum(campaign._get_objective_amounts())

    def _get_objective_amounts(self):
        self.ensure_one()
        return []

    funding_source_ids = fields.Many2many(
        "funding.source",
        string="Sources",
    )

    @api.constrains('funding_source_ids')
    def _check_funding_source_types(self):
        for campaign in self:
            if campaign.funding_source_ids:
                # Agrupar las fuentes por tipo
                sources_by_type = {}
                for source in campaign.funding_source_ids:
                    if source.source_type in sources_by_type:
                        raise ValidationError(_(
                            "You cannot add multiple funding sources of the same type. "
                            "Type '{}' is duplicated.".format(
                                dict(source._fields['source_type'].selection).get(source.source_type)
                            )
                        ))
                    sources_by_type[source.source_type] = source

    marketing_campaign_id = fields.Many2one(
        "mailing.mailing", string="Marketing Campaign", ondelete="set null"
    )
    progress = fields.Float("Progress (%)", compute="_compute_progress", store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        related="company_id.currency_id",
        store=True,
        string="Company Currency"
    )

    @api.depends("funding_source_ids", "funding_source_ids.progress", "global_objective")
    def _compute_progress(self):
        for campaign in self:
            total_raised = sum(campaign._get_raised_amounts())
            if campaign.global_objective:
                campaign.progress = (total_raised / campaign.global_objective) * 100
            else:
                campaign.progress = 0.0

    def _get_raised_amounts(self):
        self.ensure_one()
        return []

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
