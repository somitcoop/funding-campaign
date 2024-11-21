# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingSource(models.Model):
    _name = "funding.source"
    _description = "Funding Source"

    name = fields.Char("Name", required=True)
    objective = fields.Float("Objective")
    raised_amount = fields.Float("Raised Amount", compute="_compute_raised_amount")
    progress = fields.Float("Progress (%)", compute="_compute_progress")
    campaign_ids = fields.Many2many("funding.campaign", string="Campaigns")
    source_type = fields.Selection(
        selection=[
            ('default', 'Default'),
        ],
        string='Source Type',
        default='default',
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends("raised_amount", "objective")
    def _compute_progress(self):
        for source in self:
            if source.objective:
                source.progress = (source.raised_amount / source.objective) * 100
            else:
                source.progress = 0.0

    def _compute_raised_amount(self):
        for source in self:
            source.raised_amount = 0.0
