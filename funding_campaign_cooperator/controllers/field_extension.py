# -*- coding: utf-8 -*-
from odoo.addons.funding_campaign.controllers.funding_campaign import register_field_extender
import logging
import traceback

_logger = logging.getLogger(__name__)

@register_field_extender(module_name="funding_campaign_cooperator")
def extend_cooperator_fields(campaign, campaign_info):
    """Añade campos del módulo cooperator a la respuesta API de campaña"""
    _logger.debug(f"extend_cooperator_fields: START for campaign {campaign.id}")
    try:
        _logger.debug("Adding cooperator fields to campaign %s", campaign.id)
        # Añadir campos del módulo funding_campaign_cooperator si existen
        if hasattr(campaign, 'minimal_subscription_amount'):
            campaign_info["minimal_subscription_amount"] = float(campaign.minimal_subscription_amount)
            _logger.debug(f"extend_cooperator_fields: Added minimal_subscription_amount")
        if hasattr(campaign, 'maximal_subscription_amount'):
            campaign_info["maximal_subscription_amount"] = float(campaign.maximal_subscription_amount)
            _logger.debug(f"extend_cooperator_fields: Added maximal_subscription_amount")
        if hasattr(campaign, 'source_objective_subscription'):
            campaign_info["source_objective_subscription"] = float(campaign.source_objective_subscription)
            _logger.debug(f"extend_cooperator_fields: Added source_objective_subscription")
        if hasattr(campaign, 'progress_subscription'):
            campaign_info["progress_subscription"] = float(campaign.progress_subscription)
            _logger.debug(f"extend_cooperator_fields: Added progress_subscription")
        if hasattr(campaign, 'subscription_request_count'):
            campaign_info["subscription_request_count"] = campaign.subscription_request_count
            _logger.debug(f"extend_cooperator_fields: Added subscription_request_count")
        if hasattr(campaign, 'has_subscription_source'):
            campaign_info["has_subscription_source"] = campaign.has_subscription_source
            _logger.debug(f"extend_cooperator_fields: Added has_subscription_source")
    except Exception as e:
        _logger.error(f"Error extending cooperator fields: {e}")
        _logger.error(traceback.format_exc())
    finally:
        _logger.debug(f"extend_cooperator_fields: END for campaign {campaign.id}")

    return campaign_info
