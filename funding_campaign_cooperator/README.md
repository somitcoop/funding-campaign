# funding_campaign_cooperator

Link between Funding Campaigns and Cooperator modules: campaign
subscriptions create carsharing contributions deterministically, with
digital signature of the subscription agreement and SEPA-ready invoicing.

## Installation

Install via pip:

```bash
pip install odoo-addon-funding-campaign-cooperator
```

Or add the module to your Odoo addons path and install via the Apps menu.

## Configuration

- Set the cash and wallet contribution types on the share product
  (carsharing_contributions) used by each funding campaign.
- Configure the digital signature template in the funding campaign settings.

## License

AGPL-3.0 or later
