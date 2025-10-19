# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizard

def post_init_hook(cr, registry):
    """Post-initialization hook to ensure initial session exists"""
    from odoo import api, SUPERUSER_ID
    
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Ensure initial session exists
        env['stock.session']._ensure_initial_session_exists()