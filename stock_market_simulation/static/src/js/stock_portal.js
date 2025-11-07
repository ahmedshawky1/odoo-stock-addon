/* ========================================
   Stock Market Portal JavaScript
   Inspired by Wiki Design System
   ======================================== */

(function() {
    'use strict';

    // Global stock portal namespace
    window.stockPortal = window.stockPortal || {};

    // Configuration
    const CONFIG = {
        SIDEBAR_STORAGE_KEY: 'stock_sidebar_collapsed',
        NOTIFICATION_DURATION: 5000,
        API_TIMEOUT: 30000
    };

    // ================================================
    // Notification System
    // ================================================
    
    const NotificationManager = {
        container: null,
        
        init: function() {
            this.createContainer();
        },
        
        createContainer: function() {
            if (this.container) return;
            
            this.container = document.createElement('div');
            this.container.className = 'stock-notifications';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(this.container);
        },
        
        show: function(message, type = 'info', options = {}) {
            this.createContainer();
            
            const notification = document.createElement('div');
            notification.className = `stock-notification stock-notification-${type}`;
            notification.style.cssText = `
                background: white;
                border: 1px solid var(--stock-gray-200);
                border-left: 4px solid var(--color);
                border-radius: var(--stock-radius);
                padding: 1rem;
                margin-bottom: 0.5rem;
                box-shadow: var(--stock-shadow-lg);
                animation: slideInRight 0.3s ease-out;
                cursor: pointer;
            `;
            
            // Set color based on type
            const colors = {
                success: 'var(--stock-success)',
                error: 'var(--stock-danger)',
                warning: 'var(--stock-warning)',
                info: 'var(--stock-info)'
            };
            notification.style.setProperty('--color', colors[type] || colors.info);
            
            // Create icon
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };
            
            notification.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                    <i class="fa ${icons[type] || icons.info}" style="color: var(--color); margin-top: 0.125rem;"></i>
                    <div style="flex: 1;">
                        <div style="font-weight: 500; color: var(--stock-gray-900); margin-bottom: 0.25rem;">
                            ${this.getTypeLabel(type)}
                        </div>
                        <div style="color: var(--stock-gray-700); font-size: 0.875rem; line-height: 1.4;">
                            ${message}
                        </div>
                    </div>
                    <button style="border: none; background: none; color: var(--stock-gray-400); cursor: pointer; padding: 0; font-size: 1.25rem;" onclick="this.parentElement.parentElement.remove()">
                        <i class="fa fa-times"></i>
                    </button>
                </div>
            `;
            
            // Click to dismiss
            notification.addEventListener('click', function() {
                notification.remove();
            });
            
            this.container.appendChild(notification);
            
            // Auto remove after duration
            const duration = options.duration || CONFIG.NOTIFICATION_DURATION;
            if (duration > 0) {
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.style.animation = 'slideOutRight 0.3s ease-in';
                        setTimeout(() => notification.remove(), 300);
                    }
                }, duration);
            }
            
            return notification;
        },
        
        getTypeLabel: function(type) {
            const labels = {
                success: 'Success',
                error: 'Error',
                warning: 'Warning',
                info: 'Information'
            };
            return labels[type] || labels.info;
        }
    };

    // ================================================
    // Sidebar Management
    // ================================================
    
    const SidebarManager = {
        sidebar: null,
        toggle: null,
        isCollapsed: false,
        
        init: function() {
            this.sidebar = document.querySelector('.stock-sidebar');
            this.toggle = document.querySelector('.stock-sidebar-toggle');
            
            if (!this.sidebar) return;
            
            // Load saved state
            this.loadState();
            
            // Bind events
            this.bindEvents();
            
            // Set active navigation
            this.setActiveNavigation();
        },
        
        bindEvents: function() {
            if (this.toggle) {
                this.toggle.addEventListener('click', () => this.toggleSidebar());
            }
            
            // Mobile menu handling
            const mobileToggle = document.querySelector('.mobile-sidebar-toggle');
            if (mobileToggle) {
                mobileToggle.addEventListener('click', () => this.toggleMobileSidebar());
            }
            
            // Close mobile sidebar when clicking outside
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 768 && 
                    !this.sidebar.contains(e.target) && 
                    !e.target.closest('.mobile-sidebar-toggle')) {
                    this.closeMobileSidebar();
                }
            });
            
            // Handle window resize
            window.addEventListener('resize', () => {
                if (window.innerWidth > 768) {
                    this.sidebar.classList.remove('mobile-open');
                }
            });
        },
        
        toggleSidebar: function() {
            this.isCollapsed = !this.isCollapsed;
            this.updateSidebarState();
            this.saveState();
        },
        
        toggleMobileSidebar: function() {
            this.sidebar.classList.toggle('mobile-open');
        },
        
        closeMobileSidebar: function() {
            this.sidebar.classList.remove('mobile-open');
        },
        
        updateSidebarState: function() {
            if (this.isCollapsed) {
                this.sidebar.classList.add('collapsed');
                this.addTooltips();
            } else {
                this.sidebar.classList.remove('collapsed');
                this.removeTooltips();
            }
        },
        
        addTooltips: function() {
            // Add tooltip attributes to nav links when collapsed
            const navLinks = this.sidebar.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                const textEl = link.querySelector('.nav-text');
                if (textEl && textEl.textContent.trim()) {
                    link.setAttribute('data-tooltip', textEl.textContent.trim());
                }
            });
        },
        
        removeTooltips: function() {
            // Remove tooltip attributes when expanded
            const navLinks = this.sidebar.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.removeAttribute('data-tooltip');
            });
        },
        
        loadState: function() {
            const saved = localStorage.getItem(CONFIG.SIDEBAR_STORAGE_KEY);
            this.isCollapsed = saved === 'true';
            this.updateSidebarState();
        },
        
        saveState: function() {
            localStorage.setItem(CONFIG.SIDEBAR_STORAGE_KEY, this.isCollapsed.toString());
        },
        
        setActiveNavigation: function() {
            const currentPath = window.location.pathname;
            const navLinks = this.sidebar.querySelectorAll('.nav-link');
            
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === currentPath || 
                    currentPath.startsWith(link.getAttribute('href'))) {
                    link.classList.add('active');
                }
            });
        }
    };

    // ================================================
    // Order Form Management
    // ================================================
    
    const OrderFormManager = {
        form: null,
        
        init: function() {
            this.form = document.querySelector('.stock-order-form');
            if (!this.form) return;
            
            this.bindEvents();
            this.initializeForm();
        },
        
        bindEvents: function() {
            // Order type tabs
            const tabs = this.form.querySelectorAll('.tab-btn');
            tabs.forEach(tab => {
                tab.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.switchOrderType(tab);
                });
            });
            
            // Form inputs
            const inputs = this.form.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.addEventListener('input', () => this.updateOrderSummary());
                input.addEventListener('change', () => this.updateOrderSummary());
            });
            
            // Form submission
            const submitBtn = this.form.querySelector('.btn-submit');
            if (submitBtn) {
                submitBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.submitOrder();
                });
            }
        },
        
        switchOrderType: function(activeTab) {
            // Update tab states
            const tabs = this.form.querySelectorAll('.tab-btn');
            tabs.forEach(tab => tab.classList.remove('active'));
            activeTab.classList.add('active');
            
            // Update form fields based on order type
            const orderType = activeTab.dataset.type;
            this.updateFormForOrderType(orderType);
            this.updateOrderSummary();
        },
        
        updateFormForOrderType: function(orderType) {
            const priceField = this.form.querySelector('[name="price"]');
            const priceGroup = priceField?.closest('.form-group');
            
            if (orderType === 'market') {
                if (priceGroup) priceGroup.style.display = 'none';
            } else {
                if (priceGroup) priceGroup.style.display = 'block';
            }
        },
        
        updateOrderSummary: function() {
            const security = this.form.querySelector('[name="security_id"]')?.value;
            const side = this.form.querySelector('.tab-btn.active')?.dataset.side;
            const quantity = parseFloat(this.form.querySelector('[name="quantity"]')?.value || 0);
            const price = parseFloat(this.form.querySelector('[name="price"]')?.value || 0);
            const orderType = this.form.querySelector('.tab-btn.active')?.dataset.type;
            
            const summary = this.form.querySelector('.order-summary');
            if (!summary) return;
            
            // Calculate values
            const totalValue = quantity * price;
            const commission = totalValue * 0.001; // 0.1% commission
            const totalCost = side === 'buy' ? totalValue + commission : totalValue - commission;
            
            // Update summary display
            summary.innerHTML = `
                <div class="summary-row">
                    <span class="label">Side:</span>
                    <span class="value text-${side === 'buy' ? 'buy' : 'sell'}">${side ? side.toUpperCase() : '-'}</span>
                </div>
                <div class="summary-row">
                    <span class="label">Quantity:</span>
                    <span class="value">${quantity.toLocaleString()}</span>
                </div>
                <div class="summary-row">
                    <span class="label">Price:</span>
                    <span class="value">${orderType === 'market' ? 'Market Price' : '$' + price.toFixed(2)}</span>
                </div>
                <div class="summary-row">
                    <span class="label">Value:</span>
                    <span class="value">$${totalValue.toFixed(2)}</span>
                </div>
                <div class="summary-row">
                    <span class="label">Commission:</span>
                    <span class="value">$${commission.toFixed(2)}</span>
                </div>
                <div class="summary-row">
                    <span class="label">Total ${side === 'buy' ? 'Cost' : 'Proceeds'}:</span>
                    <span class="value">$${totalCost.toFixed(2)}</span>
                </div>
            `;
        },
        
        initializeForm: function() {
            // Set default tab
            const defaultTab = this.form.querySelector('.tab-btn');
            if (defaultTab) {
                this.switchOrderType(defaultTab);
            }
        },
        
        submitOrder: function() {
            const formData = new FormData(this.form);
            const side = this.form.querySelector('.tab-btn.active')?.dataset.side;
            const orderType = this.form.querySelector('.tab-btn.active')?.dataset.type;
            
            formData.append('side', side);
            formData.append('order_type', orderType);
            
            // Show loading state
            const submitBtn = this.form.querySelector('.btn-submit');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Placing Order...';
            
            // Submit via fetch
            fetch('/market/order/submit', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    NotificationManager.show('Order placed successfully!', 'success');
                    this.form.reset();
                    this.updateOrderSummary();
                    // Optionally redirect or update UI
                    if (data.redirect) {
                        setTimeout(() => window.location.href = data.redirect, 1000);
                    }
                } else {
                    NotificationManager.show(data.error || 'Failed to place order', 'error');
                }
            })
            .catch(error => {
                console.error('Order submission error:', error);
                NotificationManager.show('Network error. Please try again.', 'error');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
        }
    };

    // ================================================
    // Market Data Manager
    // ================================================
    
    const MarketDataManager = {
        updateInterval: null,
        
        init: function() {
            this.startRealTimeUpdates();
            this.bindMarketDataEvents();
        },
        
        startRealTimeUpdates: function() {
            // Update market data every 5 seconds
            this.updateInterval = setInterval(() => {
                this.updateMarketData();
            }, 5000);
            
            // Initial update
            this.updateMarketData();
        },
        
        updateMarketData: function() {
            fetch('/market/data/update', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateMarketDisplay(data.data);
                }
            })
            .catch(error => {
                console.warn('Market data update failed:', error);
            });
        },
        
        updateMarketDisplay: function(marketData) {
            // Update stat cards
            this.updateStatCards(marketData.stats);
            
            // Update market list
            this.updateMarketList(marketData.securities);
            
            // Update any price displays
            this.updatePriceDisplays(marketData.securities);
        },
        
        updateStatCards: function(stats) {
            Object.keys(stats).forEach(key => {
                const card = document.querySelector(`[data-stat="${key}"]`);
                if (card) {
                    const valueEl = card.querySelector('.stat-value');
                    const changeEl = card.querySelector('.stat-change');
                    
                    if (valueEl) valueEl.textContent = stats[key].value;
                    if (changeEl && stats[key].change !== undefined) {
                        changeEl.textContent = stats[key].change;
                        changeEl.className = `stat-change ${stats[key].change >= 0 ? 'positive' : 'negative'}`;
                    }
                }
            });
        },
        
        updateMarketList: function(securities) {
            const marketList = document.querySelector('.market-list');
            if (!marketList) return;
            
            securities.forEach(security => {
                const item = marketList.querySelector(`[data-security="${security.id}"]`);
                if (item) {
                    const priceEl = item.querySelector('.price');
                    const changeEl = item.querySelector('.price-change');
                    
                    if (priceEl) priceEl.textContent = '$' + security.current_price.toFixed(2);
                    if (changeEl) {
                        changeEl.textContent = security.change_percent.toFixed(2) + '%';
                        changeEl.className = `price-change ${security.change_percent >= 0 ? 'positive' : 'negative'}`;
                    }
                }
            });
        },
        
        updatePriceDisplays: function(securities) {
            securities.forEach(security => {
                const displays = document.querySelectorAll(`[data-price-display="${security.symbol}"]`);
                displays.forEach(display => {
                    display.textContent = '$' + security.current_price.toFixed(2);
                });
            });
        },
        
        bindMarketDataEvents: function() {
            // Security selection
            const marketItems = document.querySelectorAll('.market-item');
            marketItems.forEach(item => {
                item.addEventListener('click', () => {
                    const securityId = item.dataset.security;
                    const symbol = item.dataset.symbol;
                    this.selectSecurity(securityId, symbol);
                });
            });
        },
        
        selectSecurity: function(securityId, symbol) {
            const securitySelect = document.querySelector('[name="security_id"]');
            if (securitySelect) {
                securitySelect.value = securityId;
                
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                securitySelect.dispatchEvent(event);
                
                NotificationManager.show(`Selected ${symbol}`, 'info', { duration: 2000 });
            }
        },
        
        destroy: function() {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
            }
        }
    };

    // ================================================
    // Utility Functions
    // ================================================
    
    const Utils = {
        formatCurrency: function(amount, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },
        
        formatPercent: function(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'percent',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(value / 100);
        },
        
        formatNumber: function(value) {
            return new Intl.NumberFormat('en-US').format(value);
        },
        
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };

    // ================================================
    // Loading Manager
    // ================================================
    
    const LoadingManager = {
        show: function(target = document.body) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            `;
            
            overlay.innerHTML = `
                <div style="text-align: center;">
                    <div class="loading-spinner" style="width: 40px; height: 40px; margin: 0 auto 1rem;"></div>
                    <div style="color: var(--stock-gray-600); font-size: 0.875rem;">Loading...</div>
                </div>
            `;
            
            if (target === document.body || target.style.position === 'static') {
                target.style.position = 'relative';
            }
            
            target.appendChild(overlay);
            return overlay;
        },
        
        hide: function(overlay) {
            if (overlay && overlay.parentElement) {
                overlay.remove();
            }
        }
    };

    // ================================================
    // Main Initialization
    // ================================================
    
    function initializeStockPortal() {
        // Initialize components
        NotificationManager.init();
        SidebarManager.init();
        OrderFormManager.init();
        MarketDataManager.init();
        
        // Expose utilities globally
        window.stockPortal.utils = Utils;
        window.stockPortal.notifications = NotificationManager;
        window.stockPortal.loading = LoadingManager;
        
        // Add CSS animations
        addAnimationStyles();
        
        console.log('Stock Market Portal initialized successfully');
    }
    
    function addAnimationStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeStockPortal);
    } else {
        initializeStockPortal();
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        MarketDataManager.destroy();
    });

})();