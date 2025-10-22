#!/usr/bin/env python3

import sys
import os

# Add Odoo to path
sys.path.append('/usr/lib/python3/dist-packages')

import odoo
from odoo import SUPERUSER_ID
from odoo.api import Environment

def populate_session_numbers():
    odoo.tools.config.parse_config(['-d', 'stock', '--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=myodoo'])
    
    with odoo.registry('stock').cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        
        # Get all sessions without session_number, ordered by ID (creation order)
        sessions = env['stock.session'].search([('session_number', '=', False)], order='id')
        print(f'Found {len(sessions)} sessions without session_number')
        
        # Assign session numbers sequentially
        for i, session in enumerate(sessions, 1):
            session.session_number = i
            print(f'Assigned session_number {i} to session {session.name}')
        
        cr.commit()
        print('Session numbers populated successfully!')

if __name__ == '__main__':
    populate_session_numbers()