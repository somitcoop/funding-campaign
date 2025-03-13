import json
from datetime import datetime, date
from odoo import http, api
from odoo.http import request, Response
from odoo.exceptions import AccessDenied
import logging
import traceback
from odoo.addons.swagger_docs.controllers.swagger_controller import spec

_logger = logging.getLogger(__name__)

# Lista global para registrar extensores de campos
FIELD_EXTENDERS = {}  # Cambiamos a un diccionario para mejor organización

def register_field_extender(extender_function=None, module_name=None):
    """
    Registra una función que extiende los campos de la campaña en la respuesta API.

    Args:
        extender_function: Función que extiende los campos
        module_name: Nombre del módulo que registra el extensor

    La función debe:
    - Aceptar dos parámetros: campaign (el registro) y campaign_info (diccionario)
    - Devolver el diccionario campaign_info modificado
    """
    def decorator(func):
        mod_name = module_name or func.__module__.split('.')[0]
        FIELD_EXTENDERS[mod_name] = func
        _logger.info(f"Registered field extender: {func.__name__} from module {mod_name}")
        return func

    # Permite usar como decorador con o sin parámetros
    if extender_function is not None:
        return decorator(extender_function)
    return decorator


def apply_field_extenders(campaign, campaign_info):
    """Aplica todos los extensores registrados a la información de la campaña"""
    _logger.debug(f"Applying {len(FIELD_EXTENDERS)} field extenders: {list(FIELD_EXTENDERS.keys())}")

    for module_name, extender in FIELD_EXTENDERS.items():
        _logger.debug(f"Trying to apply extender from module {module_name}")
        try:
            campaign_info = extender(campaign, campaign_info)
            _logger.debug(f"Applied extender from module {module_name}")
        except Exception as e:
            _logger.error(f"Error applying field extender from {module_name}: {str(e)}")
            _logger.error(traceback.format_exc())

    return campaign_info


class FundingCampaignApi(http.Controller):
    def _check_auth(self, headers):
        """Helper method for authentication"""
        db = headers.get("X-Odoo-Db")
        username = headers.get("X-Odoo-Username")
        api_key = headers.get("X-Odoo-Api-Key")

        if not all([db, username, api_key]):
            return None, {
                "error": "Missing authentication parameters",
                "status": "error",
            }

        request.session.db = db
        user = (
            request.env["res.users"].sudo().search([("login", "=", username)], limit=1)
        )

        if not user:
            return None, {"error": "User not found", "status": "error"}

        try:
            temp_env = request.env(user=user.id)
            temp_env.user._check_credentials(api_key, {"interactive": False})
            return temp_env, None
        except AccessDenied:
            return None, {"error": "Authentication failed", "status": "error"}

    @http.route("/api/campaign", type="http", auth="none", csrf=False, methods=["GET"])
    def list_campaigns(self, **kw):
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        try:
            env, error = self._check_auth(request.httprequest.headers)
            if error:
                return Response(
                    json.dumps(error),
                    status=401,
                    mimetype="application/json",
                )

            request.env = env
            try:
                campaigns = request.env["funding.campaign"].search([])
                campaign_data = []
                for campaign in campaigns:
                    # Crear información base de la campaña
                    campaign_info = {
                        "id": campaign.id,
                        "name": campaign.name,
                        "description": campaign.description or "",
                        "start_date": campaign.start_date,
                        "end_date": campaign.end_date,
                        "is_permanent": campaign.is_permanent,
                        "state": campaign.state,
                        "global_objective": float(campaign.global_objective),
                        "progress": float(campaign.progress),
                        "has_donation_source": campaign.has_donation_source,
                        "donation_raised_amount": float(campaign.donation_raised_amount) if hasattr(campaign, 'donation_raised_amount') else 0.0,
                        "source_objective_donation": float(campaign.source_objective_donation) if hasattr(campaign, 'source_objective_donation') else 0.0,
                        "progress_donation": float(campaign.progress_donation) if hasattr(campaign, 'progress_donation') else 0.0,
                        "donation_count": campaign.donation_count,
                        "minimal_donation_amount": float(campaign.minimal_donation_amount) if hasattr(campaign, 'minimal_donation_amount') else 0.0,
                        "donation_request_count": campaign.donation_request_count,
                    }

                    # Aplicar los extensores registrados
                    campaign_info = apply_field_extenders(campaign, campaign_info)
                    campaign_data.append(campaign_info)

                return Response(
                    json.dumps(
                        {"status": "success", "data": campaign_data}, default=json_serial
                    ),
                    mimetype="application/json",
                )
            except Exception as model_error:
                _logger.error("Error accessing campaigns: %s", traceback.format_exc())
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Error accessing campaigns",
                        "details": str(model_error)
                    }),
                    status=500,
                    mimetype="application/json",
                )

        except Exception as e:
            _logger.error("Unexpected error: %s", traceback.format_exc())
            return Response(
                json.dumps({
                    "status": "error",
                    "message": "Unexpected error in API",
                    "details": str(e)
                }),
                status=500,
                mimetype="application/json",
            )

    @http.route(
        "/api/campaign/<int:campaign_id>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_campaign(self, campaign_id, **kwargs):
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        try:
            if not isinstance(campaign_id, int) or campaign_id <= 0:
                return Response(
                    json.dumps({"status": "error", "message": "Invalid campaign ID"}),
                    status=400,
                    mimetype="application/json",
                )

            env, error = self._check_auth(request.httprequest.headers)
            if error:
                return Response(
                    json.dumps(error),
                    status=401,
                    mimetype="application/json",
                )

            request.env = env
            campaign = request.env["funding.campaign"].browse(campaign_id)

            if not campaign.exists():
                return Response(
                    json.dumps({"status": "error", "message": "Campaign not found"}),
                    status=404,
                    mimetype="application/json",
                )

            # Crear información base de la campaña
            campaign_data = {
                "id": campaign.id,
                "name": campaign.name,
                "description": campaign.description or "",
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "is_permanent": campaign.is_permanent,
                "state": campaign.state,
                "global_objective": float(campaign.global_objective),
                "progress": float(campaign.progress),
                "progress_percentage": (
                    round(
                        (float(campaign.current_amount) / float(campaign.target_amount))
                        * 100,
                        2,
                    )
                    if campaign.target_amount
                    else 0
                ),
                "has_donation_source": campaign.has_donation_source,
                "donation_raised_amount": float(campaign.donation_raised_amount) if hasattr(campaign, 'donation_raised_amount') else 0.0,
                "source_objective_donation": float(campaign.source_objective_donation) if hasattr(campaign, 'source_objective_donation') else 0.0,
                "progress_donation": float(campaign.progress_donation) if hasattr(campaign, 'progress_donation') else 0.0,
                "donation_count": campaign.donation_count,
                "minimal_donation_amount": float(campaign.minimal_donation_amount) if hasattr(campaign, 'minimal_donation_amount') else 0.0,
                "donation_request_count": campaign.donation_request_count,
            }

            # Añadir fuentes de financiación si están disponibles
            if hasattr(campaign, 'source_ids'):
                sources = []
                for source in campaign.source_ids:
                    sources.append({
                        "id": source.id,
                        "name": source.name,
                        "source_type": source.source_type if hasattr(source, 'source_type') else "",
                        "objective": float(source.objective) if hasattr(source, 'objective') else 0.0,
                        "raised_amount": float(source.raised_amount) if hasattr(source, 'raised_amount') else 0.0,
                        "progress": float(source.progress) if hasattr(source, 'progress') else 0.0,
                    })
                campaign_data["sources"] = sources

            # Aplicar los extensores registrados
            campaign_data = apply_field_extenders(campaign, campaign_data)

            return Response(
                json.dumps(
                    {"status": "success", "data": campaign_data},
                    default=json_serial
                ),
                mimetype="application/json",
            )

        except Exception as e:
            _logger.error("Unexpected error: %s", traceback.format_exc())
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                mimetype="application/json",
            )

    @http.route("/api/dbinfo", type="http", auth="none", csrf=False, methods=["GET"])
    def get_db_info(self, **kw):
        """Endpoint to get the current database name and version information."""
        try:
            # Get current database name
            db_name = http.request.db

            # Get Odoo version using release info
            import odoo
            version_info = odoo.release.version

            # Get additional information about the instance
            server_info = {
                "database_name": db_name,
                "odoo_version": version_info
            }

            # Try to get more detailed database info if possible
            try:
                if request.env and hasattr(request.env, 'cr'):
                    server_info["server_timezone"] = request.env.context.get('tz', 'UTC')
                    base_lang = request.env['ir.module.module'].sudo().search([('name', '=', 'base')], limit=1)
                    if base_lang:
                        server_info["base_module_state"] = base_lang.state
            except Exception:
                # If we can't get additional info, just continue
                pass

            return Response(
                json.dumps({
                    "status": "success",
                    "data": server_info
                }),
                mimetype="application/json",
            )
        except Exception as e:
            _logger.error("Error getting database info: %s", traceback.format_exc())
            return Response(
                json.dumps({
                    "status": "error",
                    "message": "Could not retrieve database information",
                    "details": str(e)
                }),
                status=500,
                mimetype="application/json",
            )

    @http.route(
        "/api/campaign/extenders",
        type="http",
        auth="none",
        csrf=False,
        methods=["GET"],
    )
    def list_extenders(self, **kw):
        """Endpoint para listar todos los extensores registrados (solo para diagnóstico)"""
        try:
            extenders_info = []
            for module_name, extender in FIELD_EXTENDERS.items():
                extenders_info.append({
                    "module": module_name,
                    "function": extender.__name__,
                    "module_path": extender.__module__,
                })

            return Response(
                json.dumps({
                    "status": "success",
                    "extenders_count": len(FIELD_EXTENDERS),
                    "extenders": extenders_info
                }),
                mimetype="application/json",
            )
        except Exception as e:
            _logger.error("Error listing extenders: %s", traceback.format_exc())
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                mimetype="application/json",
            )

    @http.route(
        "/api/campaign/fix_extenders",
        type="http",
        auth="none",
        csrf=False,
        methods=["GET"],
    )
    def fix_extenders(self, **kw):
        """Función de emergencia para cargar manualmente los extensores"""
        try:
            # Intentar cargar extensores desde cada módulo
            modules_to_check = [
                "funding_campaign_cooperator",
                "funding_campaign_loan",
                "funding_campaign_donation"
            ]

            results = {}
            for module_name in modules_to_check:
                results[module_name] = "Not found"
                try:
                    # Verificar si el módulo está instalado
                    if http.request.env['ir.module.module'].sudo().search(
                        [('name', '=', module_name), ('state', '=', 'installed')]):

                        # Intentar importar el extensor y registrarlo
                        if module_name == "funding_campaign_cooperator":
                            from odoo.addons.funding_campaign_cooperator.controllers.field_extension import extend_cooperator_fields
                            FIELD_EXTENDERS["funding_campaign_cooperator"] = extend_cooperator_fields
                            results[module_name] = "Registered"

                        elif module_name == "funding_campaign_loan":
                            from odoo.addons.funding_campaign_loan.controllers.field_extension import extend_loan_fields
                            FIELD_EXTENDERS["funding_campaign_loan"] = extend_loan_fields
                            results[module_name] = "Registered"

                        elif module_name == "funding_campaign_donation":
                            from odoo.addons.funding_campaign_donation.controllers.field_extension import extend_donation_fields
                            FIELD_EXTENDERS["funding_campaign_donation"] = extend_donation_fields
                            results[module_name] = "Registered"
                    else:
                        results[module_name] = "Module not installed"
                except ImportError as e:
                    results[module_name] = f"Import Error: {str(e)}"
                except Exception as e:
                    results[module_name] = f"Error: {str(e)}"

            # Verificar extenders registrados
            extenders = []
            for mod_name, extender in FIELD_EXTENDERS.items():
                extenders.append({
                    "module": mod_name,
                    "function": extender.__name__,
                    "module_path": extender.__module__,
                })

            return Response(
                json.dumps({
                    "status": "success",
                    "modules_checked": results,
                    "current_extenders": extenders
                }),
                mimetype="application/json",
            )
        except Exception as e:
            _logger.error("Error fixing extenders: %s", traceback.format_exc())
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                mimetype="application/json",
            )

    @http.route("/api/campaign/debug", type="http", auth="none", csrf=False, methods=["GET"])
    def debug_list_campaigns(self, **kw):
        """Endpoint de depuración sin autenticación para probar los extensores"""
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        try:
            # Inicializar el entorno correctamente con el usuario admin
            uid = request.env.ref('base.user_admin').id
            request.env = api.Environment(request.cr, uid, {})

            # Obtener todas las campañas
            campaigns = request.env["funding.campaign"].search([])
            campaign_data = []

            for campaign in campaigns:
                # Crear información base de la campaña
                campaign_info = {
                    "id": campaign.id,
                    "name": campaign.name,
                    "description": campaign.description or "",
                    "start_date": campaign.start_date,
                    "end_date": campaign.end_date,
                    "is_permanent": campaign.is_permanent,
                    "state": campaign.state,
                    "global_objective": float(campaign.global_objective),
                    "progress": float(campaign.progress),
                    "has_donation_source": campaign.has_donation_source,
                    "donation_raised_amount": float(campaign.donation_raised_amount) if hasattr(campaign, 'donation_raised_amount') else 0.0,
                    "source_objective_donation": float(campaign.source_objective_donation) if hasattr(campaign, 'source_objective_donation') else 0.0,
                    "progress_donation": float(campaign.progress_donation) if hasattr(campaign, 'progress_donation') else 0.0,
                    "donation_count": campaign.donation_count,
                    "minimal_donation_amount": float(campaign.minimal_donation_amount) if hasattr(campaign, 'minimal_donation_amount') else 0.0,
                    "donation_request_count": campaign.donation_request_count,
                }

                # Aplicar los extensores registrados
                _logger.debug(f"DEBUG ENDPOINT: Applying extenders to campaign {campaign.id}")
                campaign_info = apply_field_extenders(campaign, campaign_info)
                _logger.debug(f"DEBUG ENDPOINT: Final campaign_info keys: {list(campaign_info.keys())}")

                campaign_data.append(campaign_info)

            return Response(
                json.dumps(
                    {"status": "success", "data": campaign_data}, default=json_serial
                ),
                mimetype="application/json",
            )
        except Exception as e:
            _logger.error("Debug endpoint error: %s", traceback.format_exc())
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                mimetype="application/json",
            )


spec.path(
    path="/api/campaign",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "List all campaigns",
            "description": "Get a list of all funding campaigns with basic information",
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
            ],
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
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "description": {"type": "string"},
                                                "start_date": {
                                                    "type": "string",
                                                    "format": "date-time",
                                                },
                                                "end_date": {
                                                    "type": "string",
                                                    "format": "date-time",
                                                },
                                                "is_permanent": {"type": "boolean"},
                                                "state": {"type": "string"},
                                                "global_objective": {"type": "number"},
                                                "progress": {"type": "number"},
                                                "minimal_subscription_amount": {"type": "number"},
                                                "maximal_subscription_amount": {"type": "number"},
                                                "source_objective_subscription": {"type": "number"},
                                                "progress_subscription": {"type": "number"},
                                                "subscription_request_count": {"type": "integer"},
                                                "has_subscription_source": {"type": "boolean"},
                                                "minimal_loan_amount": {"type": "number"},
                                                "maximal_loan_amount": {"type": "number"},
                                                "source_objective_loan": {"type": "number"},
                                                "progress_loan": {"type": "number"},
                                                "loan_request_count": {"type": "integer"},
                                                "has_loan_source": {"type": "boolean"},
                                                "has_donation_source": {"type": "boolean"},
                                                "donation_raised_amount": {"type": "number"},
                                                "source_objective_donation": {"type": "number"},
                                                "progress_donation": {"type": "number"},
                                                "donation_count": {"type": "integer"},
                                                "minimal_donation_amount": {"type": "number"},
                                                "donation_request_count": {"type": "integer"},
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "401": {
                    "description": "Authentication failed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "status": {"type": "string", "example": "error"},
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)

spec.path(
    path="/api/campaign/{campaign_id}",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "Get campaign details",
            "description": "Get detailed information about a specific campaign",
            "parameters": [
                {
                    "in": "path",
                    "name": "campaign_id",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "ID of the campaign to retrieve",
                },
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
            ],
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
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "start_date": {
                                                "type": "string",
                                                "format": "date-time",
                                            },
                                            "end_date": {
                                                "type": "string",
                                                "format": "date-time",
                                            },
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
                                                        "source_type": {
                                                            "type": "string"
                                                        },
                                                        "objective": {"type": "number"},
                                                        "raised_amount": {
                                                            "type": "number"
                                                        },
                                                        "progress": {"type": "number"},
                                                    },
                                                },
                                            },
                                            "minimal_subscription_amount": {"type": "number"},
                                            "maximal_subscription_amount": {"type": "number"},
                                            "source_objective_subscription": {"type": "number"},
                                            "progress_subscription": {"type": "number"},
                                            "subscription_request_count": {"type": "integer"},
                                            "has_subscription_source": {"type": "boolean"},
                                            "minimal_loan_amount": {"type": "number"},
                                            "maximal_loan_amount": {"type": "number"},
                                            "source_objective_loan": {"type": "number"},
                                            "progress_loan": {"type": "number"},
                                            "loan_request_count": {"type": "integer"},
                                            "has_loan_source": {"type": "boolean"},
                                            "has_donation_source": {"type": "boolean"},
                                            "donation_raised_amount": {"type": "number"},
                                            "source_objective_donation": {"type": "number"},
                                            "progress_donation": {"type": "number"},
                                            "donation_count": {"type": "integer"},
                                            "minimal_donation_amount": {"type": "number"},
                                            "donation_request_count": {"type": "integer"},
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "401": {
                    "description": "Authentication failed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "status": {"type": "string", "example": "error"},
                                },
                            }
                        }
                    },
                },
                "404": {
                    "description": "Campaign not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)

spec.path(
    path="/api/dbinfo",
    operations={
        "get": {
            "tags": ["System"],
            "summary": "Get database information",
            "description": "Returns the current database name and Odoo version information",
            "responses": {
                "200": {
                    "description": "Database information",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "database_name": {"type": "string"},
                                            "odoo_version": {"type": "string"},
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                    "details": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)
