from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
import traceback

_logger = logging.getLogger(__name__)


class LoanRequestApi(http.Controller):
    @http.route(
        "/api/loan/campaign/create",
        type="json",
        auth="none",
        csrf=False,
    )
    def create_loan_request(self, **kw):
        try:
            db = request.httprequest.headers.get("X-Odoo-Db")
            username = request.httprequest.headers.get("X-Odoo-Username")
            api_key = request.httprequest.headers.get("X-Odoo-Api-Key")

            if not all([db, username, api_key]):
                _logger.warning("Missing authentication parameters.")
                return {"error": "Missing authentication parameters", "status": "error"}

            request.session.db = db

            _logger.info(f"Searching user: {username}")
            user = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", username)], limit=1)
            )

            if not user:
                _logger.warning(f"User not found: {username}")
                return {"error": "User not found", "status": "error"}

            try:
                user.ensure_one()
            except ValueError:
                _logger.error(f"Multiple users found with login: {username}")
                return {
                    "error": "Multiple users found with same login",
                    "status": "error",
                }

            campaign = request.env['funding.campaign'].browse(kw.get('campaign_id'))
            if not campaign.exists():
                _logger.warning(f"Campaign not found: {kw.get('campaign_id')}")
                return {'error': 'Campaign not found', 'status': 'error'}

            if campaign.state != 'open':
                _logger.warning(f"Campaign {campaign.name} is not open (current state: {campaign.state})")
                return {
                    'error': 'Campaign is not active',
                    'status': 'error',
                    'details': 'Loan requests can only be created for active campaigns'
                }

            _logger.info(f"User found: {user.name}")

            try:
                temp_env = request.env(user=user.id)
                temp_env.user._check_credentials(api_key, {"interactive": False})
                _logger.info(f"Authentication successful for user: {user.name}")
            except AccessDenied:
                _logger.warning(f"Authentication failed for user: {username}")
                return {"error": "Authentication failed", "status": "error"}

            request.env = temp_env

            required_fields = [
                "partner_id",
                "campaign_id",
                "template_id",
                "loan_amount",
                "firstname",
                "lastname",
                "email",
                "address",
                "city",
                "zip_code",
                "country_id",
            ]

            for field in required_fields:
                if field not in kw:
                    _logger.warning(f"Missing required field: {field}")
                    return {
                        "error": f"Missing required field: {field}",
                        "status": "error",
                    }

            template = request.env["funding.loan.template"].browse(kw["template_id"])
            if template.min_amount and kw["loan_amount"] < template.min_amount:
                return {
                    "error": f"Loan amount cannot be less than {template.min_amount}",
                    "status": "error",
                }
            if template.max_amount and kw["loan_amount"] > template.max_amount:
                return {
                    "error": f"Loan amount cannot be greater than {template.max_amount}",
                    "status": "error",
                }

            loan_request = request.env["funding.loan.request"].create(
                {
                    "partner_id": kw["partner_id"],
                    "campaign_id": kw["campaign_id"],
                    "template_id": kw["template_id"],
                    "loan_amount": kw["loan_amount"],
                    "firstname": kw["firstname"],
                    "lastname": kw["lastname"],
                    "email": kw["email"],
                    "address": kw["address"],
                    "city": kw["city"],
                    "zip_code": kw["zip_code"],
                    "country_id": kw["country_id"],
                    "source": kw.get("source", "api"),
                    "state": "draft",
                }
            )

            _logger.info(f"Loan request created with ID: {loan_request.id}")

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": loan_request.id,
                        "name": loan_request.name,
                        "state": loan_request.state,
                        "loan_amount": loan_request.loan_amount,
                    },
                },
            }

        except Exception as e:
            _logger.error("Unexpected error: %s", traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": 200, "message": str(e), "data": {"status": "error"}},
            }
