# -*- coding: utf-8 -*-
from odoo.addons.funding_campaign.controllers.funding_campaign import register_field_extender
import logging
import traceback

_logger = logging.getLogger(__name__)

@register_field_extender(module_name="funding_campaign_donation")
def extend_donation_fields(campaign, campaign_info):
    """Añade campos del módulo donation a la respuesta API de campaña"""
    _logger.debug(f"extend_donation_fields: START for campaign {campaign.id}")
    try:
        # Añadir campos del módulo funding_campaign_donation si existen
        if hasattr(campaign, 'has_donation_source'):
            campaign_info["has_donation_source"] = campaign.has_donation_source
            _logger.debug(f"extend_donation_fields: Added has_donation_source")
        if hasattr(campaign, 'donation_raised_amount'):
            campaign_info["donation_raised_amount"] = float(campaign.donation_raised_amount)
            _logger.debug(f"extend_donation_fields: Added donation_raised_amount")
        if hasattr(campaign, 'source_objective_donation'):
            campaign_info["source_objective_donation"] = float(campaign.source_objective_donation)
            _logger.debug(f"extend_donation_fields: Added source_objective_donation")
        if hasattr(campaign, 'progress_donation'):
            campaign_info["progress_donation"] = float(campaign.progress_donation)
            _logger.debug(f"extend_donation_fields: Added progress_donation")
        if hasattr(campaign, 'donation_count'):
            campaign_info["donation_count"] = campaign.donation_count
            _logger.debug(f"extend_donation_fields: Added donation_count")
        if hasattr(campaign, 'minimal_donation_amount'):
            campaign_info["minimal_donation_amount"] = float(campaign.minimal_donation_amount)
            _logger.debug(f"extend_donation_fields: Added minimal_donation_amount")
        if hasattr(campaign, 'donation_request_count'):
            campaign_info["donation_request_count"] = campaign.donation_request_count
            _logger.debug(f"extend_donation_fields: Added donation_request_count")
    except Exception as e:
        _logger.error(f"Error extending donation fields: {e}")
        _logger.error(traceback.format_exc())
    finally:
        _logger.debug(f"extend_donation_fields: END for campaign {campaign.id}")

    return campaign_info