# -*- coding: utf-8 -*-
from odoo.addons.swagger_docs.controllers.swagger_controller import spec

# Extender la documentación del endpoint list_campaigns para incluir campos de cooperator
spec.path(
    path="/api/campaign",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "List all campaigns",
            "description": "Get a list of all funding campaigns with information including cooperator module fields if installed",
            "responses": {
                "200": {
                    "description": "List of campaigns",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                # Propiedades base (se mantienen)
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "description": {"type": "string"},
                                                "start_date": {"type": "string", "format": "date-time"},
                                                "end_date": {"type": "string", "format": "date-time"},
                                                "is_permanent": {"type": "boolean"},
                                                "state": {"type": "string"},
                                                "global_objective": {"type": "number"},
                                                "progress": {"type": "number"},

                                                # Campos adicionales de cooperator
                                                "minimal_subscription_amount": {
                                                    "type": "number",
                                                    "description": "Minimal subscription amount (available if cooperator module is installed)"
                                                },
                                                "maximal_subscription_amount": {
                                                    "type": "number",
                                                    "description": "Maximal subscription amount (available if cooperator module is installed)"
                                                },
                                                "source_objective_subscription": {
                                                    "type": "number",
                                                    "description": "Subscription objective amount (available if cooperator module is installed)"
                                                },
                                                "progress_subscription": {
                                                    "type": "number",
                                                    "description": "Subscription progress percentage (available if cooperator module is installed)"
                                                },
                                                "subscription_request_count": {
                                                    "type": "integer",
                                                    "description": "Number of subscription requests (available if cooperator module is installed)"
                                                },
                                                "has_subscription_source": {
                                                    "type": "boolean",
                                                    "description": "Has subscription source (available if cooperator module is installed)"
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)

# Extender la documentación del endpoint get_campaign para incluir campos de cooperator
spec.path(
    path="/api/campaign/{campaign_id}",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "Get campaign details",
            "description": "Get detailed information about a specific campaign, including cooperator module fields if installed",
            "responses": {
                "200": {
                    "description": "Campaign details",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            # Propiedades base (se mantienen)
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "start_date": {"type": "string", "format": "date-time"},
                                            "end_date": {"type": "string", "format": "date-time"},
                                            "is_permanent": {"type": "boolean"},
                                            "state": {"type": "string"},
                                            "global_objective": {"type": "number"},
                                            "progress": {"type": "number"},
                                            "progress_percentage": {"type": "number"},
                                            "sources": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"},
                                                        "source_type": {"type": "string"},
                                                        "objective": {"type": "number"},
                                                        "raised_amount": {"type": "number"},
                                                        "progress": {"type": "number"},
                                                    },
                                                },
                                            },

                                            # Campos adicionales de cooperator
                                            "minimal_subscription_amount": {
                                                "type": "number",
                                                "description": "Minimal subscription amount (available if cooperator module is installed)"
                                            },
                                            "maximal_subscription_amount": {
                                                "type": "number",
                                                "description": "Maximal subscription amount (available if cooperator module is installed)"
                                            },
                                            "source_objective_subscription": {
                                                "type": "number",
                                                "description": "Subscription objective amount (available if cooperator module is installed)"
                                            },
                                            "progress_subscription": {
                                                "type": "number",
                                                "description": "Subscription progress percentage (available if cooperator module is installed)"
                                            },
                                            "subscription_request_count": {
                                                "type": "integer",
                                                "description": "Number of subscription requests (available if cooperator module is installed)"
                                            },
                                            "has_subscription_source": {
                                                "type": "boolean",
                                                "description": "Has subscription source (available if cooperator module is installed)"
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)