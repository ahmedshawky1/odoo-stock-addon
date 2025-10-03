# Bug Fix: Invalid Field Error on Session Start/Close

## Issue
**Error**: `ValueError: Invalid field stock.security.status in leaf ('status', 'not in', ['liquidated', 'expired'])`

**When**: Starting or closing a session via UI button clicks

**Root Cause**: The `stock.session` model was trying to filter `stock.security` records by a `status` field that doesn't exist. The `stock.security` model only has an `active` field (Boolean).

---

## Error Details

### Original Error Traceback
```
ValueError: Invalid field stock.security.status in leaf ('status', 'not in', ['liquidated', 'expired'])
  File ".../models/stock_session.py", line 209, in action_open_session
    active_securities = self.env['stock.security'].search([
        ('status', 'not in', ['liquidated', 'expired'])
    ])
```

### Locations Found
1. `action_open_session()` - Line 209
2. `action_close_session()` - Line 254

---

## Solution

### Changed Domain Filter

**Before (WRONG)**:
```python
active_securities = self.env['stock.security'].search([
    ('status', 'not in', ['liquidated', 'expired'])
])
```

**After (CORRECT)**:
```python
active_securities = self.env['stock.security'].search([
    ('active', '=', True)
])
```

### Why This Works

The `stock.security` model has:
- ✅ `active` field (Boolean) - Standard Odoo field for archiving records
- ❌ No `status` field

The `active` field serves the same purpose:
- `active=True` → Security is available for trading
- `active=False` → Security is archived/inactive (equivalent to liquidated/expired)

---

## Files Modified

### 1. `models/stock_session.py` - Line ~209
**Method**: `action_open_session()`

**Change**:
```python
# Set session start prices for all active securities
# Matches C#: "SELECT Row_ID, price FROM stocks WHERE status<>'liquidated'"
active_securities = self.env['stock.security'].search([
    ('active', '=', True)  # Changed from ('status', 'not in', ['liquidated', 'expired'])
])
```

### 2. `models/stock_session.py` - Line ~254
**Method**: `action_close_session()`

**Change**:
```python
# Record price history snapshots for all active securities
# Matches C#: Insert into stockpricehistory/bondpricehistory
active_securities = self.env['stock.security'].search([
    ('active', '=', True)  # Changed from ('status', 'not in', ['liquidated', 'expired'])
])
```

---

## Testing

### Manual Test Steps
1. ✅ Open a draft session
2. ✅ Click "Start Session" button
3. ✅ Verify no error occurs
4. ✅ Check securities have `session_start_price` and `price_to_compare_with` updated
5. ✅ Click "Close Session" button
6. ✅ Verify no error occurs
7. ✅ Check price history records created

### Expected Behavior
- Session starts successfully
- All active securities get their prices updated
- Session closes successfully
- Price history snapshots are created for all active securities

---

## Related Information

### C# Reference Comment
The original C# code comment mentioned:
```sql
SELECT Row_ID, price FROM stocks WHERE status<>'liquidated'
```

However, in Odoo, we use the `active` field pattern instead of a `status` field on securities.

### Field Comparison

**C# `stocks` Table**:
- Has `status` column with values: 'active', 'liquidated', 'expired'

**Odoo `stock.security` Model**:
- Has `active` field (Boolean)
- Has `security_type` field ('stock', 'bond', 'mf')
- Does NOT have `status` field

---

## Prevention

To avoid similar issues in the future:

1. **Check Model Fields**: Always verify field existence before using in domains
2. **Use `active` Pattern**: For enable/disable functionality, use Odoo's standard `active` field
3. **Reference Mapping**: Document C# → Odoo field mappings when different naming is used

---

## Deployment

**Status**: ✅ Fixed and Deployed

**Version**: 1.0.2 (same version, hot-fix)

**Commands Run**:
```bash
sudo docker restart odoo_stock
sudo docker exec -it odoo_stock odoo -u stock_market_simulation -d stock --stop-after-init
```

**Deployment Result**: 
- Module upgraded successfully
- Database tables updated
- No errors
- 953 queries executed in 2.61s

---

## Impact

### Before Fix
- ❌ Cannot start sessions (ValueError crash)
- ❌ Cannot close sessions (ValueError crash)
- ❌ Portal users see server error
- ❌ Session workflow completely broken

### After Fix
- ✅ Sessions start normally
- ✅ Sessions close normally  
- ✅ Securities prices update correctly
- ✅ Price history records created
- ✅ Full session workflow functional

---

## Summary

**Problem**: Used non-existent `status` field on `stock.security`  
**Solution**: Changed to use standard `active` field  
**Result**: Session start/close functionality restored  
**Time to Fix**: ~5 minutes  
**Deployment**: Successful
