# -*- coding: utf-8 -*-
from odoo.addons.funding_campaign.controllers.funding_campaign import register_field_extender
import logging
import traceback

_logger = logging.getLogger(__name__)

@register_field_extender(module_name="funding_campaign_loan")
def extend_loan_fields(campaign, campaign_info):
    """Añade campos del módulo loan a la respuesta API de campaña"""
    _logger.debug(f"extend_loan_fields: START for campaign {campaign.id}")
    try:
        # Añadir campos del módulo funding_campaign_loan si existen
        if hasattr(campaign, 'minimal_loan_amount'):
            campaign_info["minimal_loan_amount"] = float(campaign.minimal_loan_amount)
            _logger.debug(f"extend_loan_fields: Added minimal_loan_amount")
        if hasattr(campaign, 'maximal_loan_amount'):
            campaign_info["maximal_loan_amount"] = float(campaign.maximal_loan_amount)
            _logger.debug(f"extend_loan_fields: Added maximal_loan_amount")
        if hasattr(campaign, 'source_objective_loan'):
            campaign_info["source_objective_loan"] = float(campaign.source_objective_loan)
            _logger.debug(f"extend_loan_fields: Added source_objective_loan")
        if hasattr(campaign, 'progress_loan'):
            campaign_info["progress_loan"] = float(campaign.progress_loan)
            _logger.debug(f"extend_loan_fields: Added progress_loan")
        if hasattr(campaign, 'loan_request_count'):
            campaign_info["loan_request_count"] = campaign.loan_request_count
            _logger.debug(f"extend_loan_fields: Added loan_request_count")
        if hasattr(campaign, 'has_loan_source'):
            campaign_info["has_loan_source"] = campaign.has_loan_source
            _logger.debug(f"extend_loan_fields: Added has_loan_source")
    except Exception as e:
        _logger.error(f"Error extending loan fields: {e}")
        _logger.error(traceback.format_exc())
    finally:
        _logger.debug(f"extend_loan_fields: END for campaign {campaign.id}")

    return campaign_info
