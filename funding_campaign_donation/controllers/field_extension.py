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
        # Usar getattr con valores por defecto para evitar AttributeError
        campaign_info["has_donation_source"] = getattr(campaign, 'has_donation_source', False)
        _logger.debug(f"extend_donation_fields: Added has_donation_source = {campaign_info['has_donation_source']}")
        
        campaign_info["donation_raised_amount"] = float(getattr(campaign, 'donation_raised_amount', 0.0))
        _logger.debug(f"extend_donation_fields: Added donation_raised_amount")
        
        campaign_info["source_objective_donation"] = float(getattr(campaign, 'source_objective_donation', 0.0))
        _logger.debug(f"extend_donation_fields: Added source_objective_donation")
        
        campaign_info["progress_donation"] = float(getattr(campaign, 'progress_donation', 0.0))
        _logger.debug(f"extend_donation_fields: Added progress_donation")
        
        campaign_info["donation_count"] = getattr(campaign, 'donation_count', 0)
        _logger.debug(f"extend_donation_fields: Added donation_count")
        
        campaign_info["minimal_donation_amount"] = float(getattr(campaign, 'minimal_donation_amount', 0.0))
        _logger.debug(f"extend_donation_fields: Added minimal_donation_amount")
        
        campaign_info["donation_request_count"] = getattr(campaign, 'donation_request_count', 0)
        _logger.debug(f"extend_donation_fields: Added donation_request_count")
        
    except Exception as e:
        _logger.error(f"Error extending donation fields: {e}")
        _logger.error(traceback.format_exc())
    finally:
        _logger.debug(f"extend_donation_fields: END for campaign {campaign.id}")

    return campaign_info