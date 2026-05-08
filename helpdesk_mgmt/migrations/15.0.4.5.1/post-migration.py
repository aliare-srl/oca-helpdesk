def migrate(cr, version):
    cr.execute("""
        ALTER TABLE helpdesk_ticket
        ADD COLUMN IF NOT EXISTS portal_notification_sent boolean DEFAULT false;
    """)
