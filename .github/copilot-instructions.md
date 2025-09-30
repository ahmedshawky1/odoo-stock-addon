# Odoo 18 stock Module - Development Guide

## Core Rules
- we are converting this from C# code to odoo module , C# code is reference only path "/var/STOCK_SOURCE_FILES" check their for reference
- **Always** restart container + upgrade module after ANY changes
- **Portal-first**: Apply changes to portal views unless specified otherwise  
- **No @import**: Use asset bundle loading order in `__manifest__.py`
- **Git**: Only commit when user requests

## Quick Commands
```bash
# After any change (MANDATORY):
sudo docker restart odoo_stock
sudo docker exec -it odoo_stock odoo -u stock_market_simulation -d stock --stop-after-init
```

## Code Patterns

**Models**: `_inherit = ['mail.thread', 'mail.activity.mixin']` + `tracking=True` on key fields  
**Views**: Use `<list>` not `<tree>`, `<chatter/>` not `<div class="oe_chatter">`  
**APIs**: Return `{'success': bool, 'data/error': str}` from JSON endpoints

## Critical Fixes

### XML & JS
```xml
<!-- ✅ JS in XML: wrap in CDATA -->
## Critical Fixes

### JavaScript
- **JS in XML**: Wrap in `<script>//<![CDATA[ ... //]]></script>`
- **Event handlers**: Use `addEventListener` in `DOMContentLoaded`, not inline `onclick`
- **Event delegation**: For dynamic content, use `event.target.closest('.btn-class')`
- **Data attributes**: `t-att-data-page-id="page.id"` for frontend communication

### Bootstrap Modals
- Place modal in same template as trigger button
- Use `data-bs-toggle="modal"` attributes, not inline handlers
- Load data on `show.bs.modal` event
- Include fallbacks for different Bootstrap versions

### Security & Performance
- Check `obj.exists()` before accessing attributes
- Use `limit=1` for single record searches
- Log errors with `_logger.error()` and return `{'success': False, 'error': str(e)}`
```

### JavaScript Function & Modal Errors
Common errors and patterns we must avoid/follow in portal templates.

**Problem A**: `ReferenceError: function is not defined` when using inline event handlers
**Cause**: Function called before it's defined in DOM order

**❌ WRONG - Inline handlers with late function definition:**
```xml
<!-- HTML element calling function -->
<select onchange="updateSomething()">...</select>
<button onclick="doAction()">Click me</button>

<!-- Function defined much later in template -->
<script>//<![CDATA[
    function updateSomething() { ... }  // Defined after HTML
    function doAction() { ... }
//]]></script>
```

**✅ CORRECT - Event listeners with DOMContentLoaded:**
```xml
<!-- Clean HTML without inline handlers -->
<select id="my_select">...</select>
<button id="my_button">Click me</button>

<!-- For dynamic content (loops), use classes instead of IDs -->
<button class="action-btn" data-item-id="123">Dynamic Button</button>

<!-- Proper event listener setup -->
<script>//<![CDATA[
    // Function definitions
    function updateSomething() { ... }
    function doAction() { ... }
    function handleDynamicAction(element) { ... }
    
    // Event listeners added after DOM loads
    document.addEventListener('DOMContentLoaded', function() {
        // Single elements by ID
        const selectElement = document.getElementById('my_select');
        if (selectElement) {
            selectElement.addEventListener('change', updateSomething);
        }
        
        const buttonElement = document.getElementById('my_button');
        if (buttonElement) {
            buttonElement.addEventListener('click', doAction);
        }
        
        // Dynamic content with event delegation
        document.addEventListener('click', function(event) {
            if (event.target.closest('.action-btn')) {
                handleDynamicAction(event.target.closest('.action-btn'));
            }
        });
    });
//]]></script>
```

**Event Delegation Pattern**: For buttons in loops (t-foreach), use:
- **Classes** instead of IDs: `class="edit-btn remove-btn"`
- **Event delegation**: Listen on document and check `event.target.closest('.btn-class')`
- **Data attributes**: Pass data via `t-att-data-item-id="item.id"`

**Benefits**: No timing issues, cleaner separation of HTML/JS, better performance, works with dynamic content

---

**Problem B**: Bootstrap modal crashes: `Cannot read properties of undefined (reading 'backdrop')`
**Causes**:
- Modal element not present in the same rendered template as the trigger button
- Multiple duplicate modals with the same `id` across templates
- Calling Bootstrap APIs too early or mixing different Bootstrap versions

**✅ CORRECT - Modal placement and triggers:**
```xml
<!-- Place modal in the SAME template as the trigger button (e.g., topic detail) -->
<button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#myModal">Open</button>

<!-- Later in that same template -->
<div class="modal fade" id="myModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content"> ... </div>
    </div>
    <!-- No duplicates of #myModal in other templates -->
</div>
```

**✅ CORRECT - Load data on show event (no inline onclick):**
```xml
<script>//<![CDATA[
document.addEventListener('DOMContentLoaded', function() {
    const modalEl = document.getElementById('myModal');
    if (modalEl) {
        modalEl.addEventListener('show.bs.modal', function() {
            // fetch and populate selects safely here
        });
    }
});
//]]></script>
```

**✅ CORRECT - Robust modal show/hide (Bootstrap 5/4 safe):**
```js
function showModal(el) {
    try {
        if (window.bootstrap && bootstrap.Modal) {
            new bootstrap.Modal(el).show();
        } else if (window.$ && $.fn.modal) {
            $(el).modal('show');
        } else {
            el.style.display = 'block';
            document.body.classList.add('modal-open');
        }
    } catch (e) { /* fallback */ }
}

function hideModal(el) {
    try {
        if (window.bootstrap && bootstrap.Modal) {
            let inst = null;
            if (typeof bootstrap.Modal.getInstance === 'function') {
                try { inst = bootstrap.Modal.getInstance(el); } catch (_) { inst = null; }
            }
            if (!inst) inst = new bootstrap.Modal(el);
            if (inst && typeof inst.hide === 'function') return inst.hide();
        }
        if (window.$ && $.fn.modal) return $(el).modal('hide');
    } catch (e) {}
    // Manual fallback
    el.style.display = 'none';
    el.classList.remove('show');
    document.body.classList.remove('modal-open');
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) backdrop.remove();
}
```

**DOs**:
- Keep a single modal per `id`; avoid duplicates across templates
- Use `data-bs-*` attributes for triggers; avoid inline `onclick` for opening modals
- Populate modal inputs on `show.bs.modal` (ensures elements exist)

**DON'Ts**:
- Don’t call `bootstrap.Modal.getInstance` without a fallback; some bundles don’t expose it
- Don’t place the modal in a different template file than its trigger
- Don’t manipulate selects/inputs before the modal is in the DOM

### Security
```python
# ✅ Robust access pattern
try:
    if hasattr(obj, '_check_access_rights') and callable(obj._check_access_rights):
        if not obj._check_access_rights():
            return request.not_found()
except Exception:
    if not request.env.user.has_group('base.group_system'):
        return request.not_found()
```

### Performance
- `limit=1` for single record searches
- `exists()` before accessing record attributes
- No f-strings in domains, use proper domain syntax
- Check existing toasts before showing new ones

### Error Handling
```python
import logging
_logger = logging.getLogger(__name__)

_logger.error(f"Error in {function} for {type} {id}: {str(e)}")
return {'success': False, 'error': f'Unable to {operation}: {str(e)}'}
```

### Frontend APIs
- **JSON-RPC**: Wrap requests in `{ jsonrpc: '2.0', method: 'call', params: {...} }`
- **Response**: Unwrap with `const payload = raw?.result || raw`
- **Errors**: Extract with `payload?.error || raw?.error?.message || 'Unknown error'`
- **Globals**: Use `window.stockPortal = {...}` namespace to avoid conflicts

### Portal Button Pattern
1. **Data attributes**: `data-item-type`, `data-page-id`, `data-topic-id` on buttons
2. **Event delegation**: `document.addEventListener('click', e => e.target.closest('.action-btn'))`
3. **Button states**: Disable on click, show spinner, restore on error
4. **Cache busting**: Module upgrade → container restart → hard refresh (Ctrl+F5)

