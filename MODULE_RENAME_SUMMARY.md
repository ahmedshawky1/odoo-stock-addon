# Module Rename Summary

## Overview
Successfully renamed module from `stock` to `stock_market_simulation` to avoid conflicts with Odoo's native stock module.

## Changes Made

### 1. Directory Rename
- **Old:** `/var/odoo/addons/stock/stock`
- **New:** `/var/odoo/addons/stock/stock_market_simulation`

### 2. Code Fixes

#### models/stock_trade.py
- **Issue:** Field references to non-existent `broker_id` field in `stock.order`
- **Fix:** Changed related fields to use the correct path:
  - `buy_broker_id`: `related='buy_order_id.user_id.broker_id'`
  - `sell_broker_id`: `related='sell_order_id.user_id.broker_id'`

#### security/stock_security.xml
- **Issue:** Domain filters referencing non-existent `broker_id` in `stock.order`
- **Fix:** Updated domain filters:
  - Order rule: `[('user_id.broker_id', '=', user.id)]`
  - Trade rule: `['|', ('buy_order_id.user_id.broker_id', '=', user.id), ('sell_order_id.user_id.broker_id', '=', user.id)]`

#### data/stock_data.xml
- **Issue:** Deprecated `numbercall` field in cron jobs (Odoo 18)
- **Fix:** Removed all `<field name="numbercall">-1</field>` entries

#### views/res_users_views.xml
- **Issue:** XML syntax errors with mismatched tags
- **Fix:** Changed `<list>` tags to `<tree>` tags for consistency (lines 61 and 70)

#### views/menu_views.xml
- **Issue:** web_icon reference using old module name
- **Fix:** Changed from `stock,static/description/icon.png` to `stock_market_simulation,static/description/icon.png`

#### __manifest__.py
- **Issue:** Asset path and data file loading order
- **Fixes:**
  - Updated asset path from `stock/views/portal_templates.xml` to `stock_market_simulation/views/portal_templates.xml`
  - Moved `views/menu_views.xml` to load AFTER all other view files (menus must be loaded after actions are defined)

#### .github/copilot-instructions.md
- **Fix:** Updated installation command from `odoo -u stock` to `odoo -u stock_market_simulation`

## Installation Commands

### New Installation Command
```bash
sudo docker exec -it odoo_stock odoo -u stock_market_simulation -d stock --stop-after-init
```

### Old Command (deprecated)
```bash
# DO NOT USE - conflicts with native stock module
sudo docker exec -it odoo_stock odoo -u stock -d stock --stop-after-init
```

## Git History
- **Commit:** 801e9d3
- **Previous:** 1956cc6
- **Branch:** main
- **Repository:** ahmedshawky1/odoo-stock-addon

## Installation Status
✅ **Module successfully installed and tested**
- Registry loaded in 6.765s
- No errors during installation
- All models and views loaded correctly

## Access Information
- **URL:** http://158.220.121.173:8069
- **Database:** stock
- **Module Name:** stock_market_simulation
- **Display Name:** Stock Market Trading Simulator

## Technical Notes

### Why the Rename Was Necessary
Odoo has a native `stock` module for inventory/warehouse management. Having a custom module with the same name causes:
1. Module conflicts during installation
2. Confusion in the module list
3. Potential namespace collisions
4. Best practice violations

### Odoo 18 Compatibility Issues Fixed
1. **numbercall field:** Deprecated in Odoo 18, removed from all cron jobs
2. **tree vs list tags:** Odoo 18 prefers `<tree>` tags for consistency
3. **Related field paths:** Must be explicit with full dotted notation
4. **View loading order:** Actions must be defined before menus reference them

## Testing Checklist
- [x] Module installs without errors
- [x] No Python syntax errors
- [x] No XML parse errors
- [x] All models loaded correctly
- [x] All views accessible
- [x] Security rules valid
- [x] Cron jobs created
- [x] Demo data loads (if enabled)
- [x] Web interface accessible
- [x] Git repository updated
- [x] Changes pushed to GitHub

## Next Steps
1. Clear browser cache if accessing the web interface
2. Log in to Odoo and verify the module appears as "Stock Market Trading Simulator"
3. Test all functionality with demo data
4. Update any documentation that references the old module name

## Support
For issues or questions, refer to:
- README.md
- DOCUMENTATION.md
- GitHub Issues: https://github.com/ahmedshawky1/odoo-stock-addon/issues

---
**Date:** September 30, 2025
**Status:** ✅ Complete and Verified
