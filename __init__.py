# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizard

def post_init_hook(env):
    """Post-initialization hook to ensure initial session exists"""
    from odoo import SUPERUSER_ID
    # Ensure initial session exists
    env['stock.session']._ensure_initial_session_exists()
    # Backfill investor cash balances if zero using their initial capital
    try:
        # Broaden backfill to include legacy users where user_type may be unset (treated as investors)
        users = env['res.users'].search([('initial_capital', '>', 0)])
        patched = 0
        for usr in users:
            # Seed only when cash is exactly zero and the user is an investor or legacy (no user_type set)
            if (not usr.cash_balance or usr.cash_balance == 0.0) and (usr.user_type in ('investor', False)):
                usr.cash_balance = usr.initial_capital
                patched += 1
        if patched:
            env.cr.commit()
    except Exception:
        # Don't block install/upgrade on backfill issues
        pass