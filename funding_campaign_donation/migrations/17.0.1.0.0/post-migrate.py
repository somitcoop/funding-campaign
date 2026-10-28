def migrate(cr, version):
    cr.execute("""
        UPDATE donation_donation
        SET campaign_id = old_campaign_id
        FROM funding_campaign
        WHERE funding_campaign.old_donation_campaign_id = donation_donation.campaign_id;
    """)
