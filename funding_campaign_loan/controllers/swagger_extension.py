# -*- coding: utf-8 -*-
from odoo.addons.swagger_docs.controllers.swagger_controller import spec

# Extender la documentación del endpoint list_campaigns para incluir campos de loan
spec.path(
    path="/api/campaign",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "List all campaigns",
            "description": "Get a list of all funding campaigns with information including loan module fields if installed",
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

                                                # Campos adicionales de loan
                                                "minimal_loan_amount": {
                                                    "type": "number",
                                                    "description": "Minimal loan amount (available if loan module is installed)"
                                                },
                                                "maximal_loan_amount": {
                                                    "type": "number",
                                                    "description": "Maximal loan amount (available if loan module is installed)"
                                                },
                                                "source_objective_loan": {
                                                    "type": "number",
                                                    "description": "Loan objective amount (available if loan module is installed)"
                                                },
                                                "progress_loan": {
                                                    "type": "number",
                                                    "description": "Loan progress percentage (available if loan module is installed)"
                                                },
                                                "loan_request_count": {
                                                    "type": "integer",
                                                    "description": "Number of loan requests (available if loan module is installed)"
                                                },
                                                "has_loan_source": {
                                                    "type": "boolean",
                                                    "description": "Has loan source (available if loan module is installed)"
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

# Extender la documentación del endpoint get_campaign para incluir campos de loan
spec.path(
    path="/api/campaign/{campaign_id}",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "Get campaign details",
            "description": "Get detailed information about a specific campaign, including loan module fields if installed",
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

                                            # Campos adicionales de loan
                                            "minimal_loan_amount": {
                                                "type": "number",
                                                "description": "Minimal loan amount (available if loan module is installed)"
                                            },
                                            "maximal_loan_amount": {
                                                "type": "number",
                                                "description": "Maximal loan amount (available if loan module is installed)"
                                            },
                                            "source_objective_loan": {
                                                "type": "number",
                                                "description": "Loan objective amount (available if loan module is installed)"
                                            },
                                            "progress_loan": {
                                                "type": "number",
                                                "description": "Loan progress percentage (available if loan module is installed)"
                                            },
                                            "loan_request_count": {
                                                "type": "integer",
                                                "description": "Number of loan requests (available if loan module is installed)"
                                            },
                                            "has_loan_source": {
                                                "type": "boolean",
                                                "description": "Has loan source (available if loan module is installed)"
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