from odoo.addons.swagger_docs.controllers.swagger_controller import spec

spec.path(
    path="/api/campaign/{campaign_id}/donation_request",
    operations={
        "post": {
            "tags": ["Campaign Donations"],
            "summary": "Create a new campaign donation request",
            "description": "Create a new donation request with the provided partner and campaign information. The API integrates with the OCA base_location module to automatically find and set the zip_id based on the provided zip_code and country_code.",
            "parameters": [
                {
                    "in": "header",
                    "name": "X-Odoo-Db",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Odoo database name",
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Username",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Username for authentication",
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Api-Key",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "API key for authentication",
                },
                {
                    "in": "path",
                    "name": "campaign_id",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "ID of the funding campaign",
                },
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": [
                                "vat",
                                "donation_amount",
                                "firstname",
                                "lastname",
                                "email",
                                "address",
                                "zip_code",
                                "lang",
                                "country_code",
                            ],
                            "properties": {
                                "vat": {
                                    "type": "string",
                                    "description": "VAT number of the donor",
                                },
                                "donation_amount": {
                                    "type": "number",
                                    "format": "float",
                                    "description": "Amount of the donation",
                                },
                                "firstname": {
                                    "type": "string",
                                    "description": "First name of the donor",
                                },
                                "lastname": {
                                    "type": "string",
                                    "description": "Last name of the donor",
                                },
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "Email address",
                                },
                                "address": {
                                    "type": "string",
                                    "description": "Street address",
                                },
                                "zip_code": {
                                    "type": "string",
                                    "description": "Postal code. Used to find the corresponding zip_id from the base_location module.",
                                },
                                "lang": {
                                    "type": "string",
                                    "description": "Language code (ISO 639-1) with optional country code (e.g. en_US, es_ES, fr_FR)",
                                    "example": "en_US",
                                    "pattern": "^[a-z]{2,3}(_[A-Z]{2})?$",
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Phone number",
                                    "required": False,
                                },
                                "country_code": {
                                    "type": "string",
                                    "description": "ISO 3166-1 alpha-2 country code (e.g. ES, FR, BE). Used with zip_code to find the corresponding location data.",
                                    "minLength": 2,
                                    "maxLength": 2,
                                },
                                "tax_receipt_option": {
                                    "type": "string",
                                    "description": "Tax receipt option",
                                    "enum": ["none", "each", "annual"],
                                    "default": "none",
                                    "required": False,
                                },
                            },
                        }
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "jsonrpc": {"type": "string", "example": "2.0"},
                                    "id": {"type": "null"},
                                    "result": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "example": "success",
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "integer",
                                                        "description": "ID of created donation request",
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Name of donation request",
                                                    },
                                                    "state": {
                                                        "type": "string",
                                                        "description": "State of donation request",
                                                    },
                                                    "donation_amount": {
                                                        "type": "number",
                                                        "format": "float",
                                                        "description": "Amount of the donation",
                                                    },
                                                    "campaign": {
                                                        "type": "object",
                                                        "properties": {
                                                            "id": {
                                                                "type": "integer",
                                                                "description": "ID of the campaign",
                                                            },
                                                            "name": {
                                                                "type": "string",
                                                                "description": "Name of the campaign",
                                                            },
                                                            "state": {
                                                                "type": "string",
                                                                "description": "State of the campaign",
                                                            },
                                                            "description": {
                                                                "type": "string",
                                                                "description": "Description of the campaign",
                                                            },
                                                            "global_objective": {
                                                                "type": "number",
                                                                "description": "Global objective of the campaign",
                                                            },
                                                            "progress": {
                                                                "type": "number",
                                                                "description": "Progress of the campaign",
                                                            },
                                                            "source_objective_donation": {
                                                                "type": "number",
                                                                "description": "Donation objective amount",
                                                            },
                                                            "donation_raised_amount": {
                                                                "type": "number",
                                                                "description": "Amount raised through donations",
                                                            },
                                                            "progress_donation": {
                                                                "type": "number",
                                                                "description": "Progress percentage of donation objective",
                                                            },
                                                            "minimal_donation_amount": {
                                                                "type": "number",
                                                                "description": "Minimum donation amount for the campaign",
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "400": {
                    "description": "Error response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "jsonrpc": {"type": "string", "example": "2.0"},
                                    "id": {"type": "null"},
                                    "error": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer"},
                                            "message": {"type": "string"},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "status": {"type": "string", "example": "error"},
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
