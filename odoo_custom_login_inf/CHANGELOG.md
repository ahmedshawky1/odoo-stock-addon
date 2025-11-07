# Changelog

## [18.0.1.3.0] - 2025-11-05

### Added - Reset Password Feature
- **Custom reset password page** matching login design and skan portal branding
- **Branded forgot password functionality** with consistent Egyptian government color scheme
- **Change password template** for email reset links with user-friendly interface
- **Custom controllers** for auth_signup override (`CustomAuthSignupHome`)
- **Consistent styling** across all authentication pages (login, reset, change password)
- **Enhanced navigation** with proper back-to-login links and clear call-to-action buttons

### Enhanced
- **Improved user experience** with consistent branding across authentication flow
- **Added Font Awesome icons** to all auth forms (key, envelope, paper-plane, shield icons)
- **Responsive design** for all authentication pages ensuring mobile compatibility
- **Better error handling** and user feedback with color-coded alert messages
- **Password requirements** display with clear guidelines for new password creation

### Technical
- Added `CustomAuthSignupHome` controller extending Odoo's `AuthSignupHome`
- Created comprehensive reset password template collection:
  - `reset_password_layout` - Base layout for reset password pages
  - `reset_password_template_dedicated` - Email input form for password reset
  - `change_password_layout` - Base layout for password change
  - `change_password_template` - New password form with confirmation
- Updated manifest dependencies and descriptions
- Enhanced CSS styling for form consistency and accessibility
- Added comprehensive documentation (`README_RESET_PASSWORD.md`)

### Security
- **CSRF Protection**: All forms include proper CSRF tokens
- **Frame Protection**: X-Frame-Options headers prevent clickjacking
- **Input Validation**: HTML5 validation with server-side checks
- **Safe Error Handling**: Error messages without sensitive information disclosure

## [18.0.1.2.0] - 2025-11-02

### Changed - Skan Portal Rebranding
- **Complete UI overhaul** to match Egyptian Real Estate Platform (skan portal) design
- Redesigned login page with modern, clean aesthetic
- Added Egyptian government color scheme (Red #C62E29)
- Integrated Bootstrap 5.1.3 for responsive layout
- Added Font Awesome 4.7 icons throughout the interface
- Implemented Cairo and Roboto font families for authentic Egyptian look
- **ENFORCED portal redirect**: Portal users are now FORCED to redirect to the configured "Portal Redirect Path" setting, ignoring any URL redirect parameters

### Added
- Skan portal navbar with logo and branding
- Gradient header design on login card
- Professional footer matching portal templates
- Custom CSS variables for consistent theming
- Enhanced form styling with focus effects
- Icon integration in form labels and buttons

### Fixed
- Portal users can no longer bypass the configured redirect path
- Internal users can still use redirect parameters normally

### Technical Details
- Updated `middle_login_layout` template with portal design
- Modified `_login_redirect()` method to force portal user redirects
- Added external CDN resources (Bootstrap, Font Awesome, Google Fonts)
- Implemented CSS variable system for easy theme customization
- Login card with header/body separation for better visual hierarchy
- Removed background image dependencies in favor of clean design

### Design Specifications
- Primary Red: #C62E29 with gradient to #9D2420
- Typography: Cairo (Arabic-friendly) and Roboto fonts
- Layout: Flexbox-based responsive design
- Shadows: Consistent shadow system for depth
- Border Radius: 8-12px for modern rounded corners

## [18.0.1.1.0] - 2025-10-30

### Added
- Portal user custom redirect path configuration
- New field in General Settings to configure portal redirect path
- Portal users can now be redirected to custom paths after login instead of default /my

### Changed
- Added portal module dependency
- Updated controller to implement custom login redirect logic for portal users
- Enhanced configuration view with portal redirect path setting

### Technical Details
- Added `portal_redirect_path` field to `res.config.settings`
- Overridden `_login_redirect` method in controller to handle portal user redirection
- Portal users are identified using `has_group('base.group_portal')`
- Internal users continue to be redirected to `/web` as before

## [18.0.1.0.0] - 2025-10-30

### Added
- Odoo 18.0 compatibility
- Improved model descriptions and field requirements
- Enhanced asset management system
- Better error handling and logging

### Changed
- Updated manifest version to 18.0.1.0.0
- Modified controllers to inherit from proper base classes
- Improved template syntax and structure
- Updated asset paths and bundle configuration
- Enhanced security configuration with descriptive names
- Improved image widget display in forms

### Fixed
- Fixed potential errors in get_values method with proper parameter validation
- Removed deprecated print statements and replaced with proper logging
- Updated import statements for Odoo 18 compatibility
- Fixed asset path references

### Technical Details
- Controllers now inherit from `WebHome` for better compatibility
- Removed deprecated `Website` controller class
- Updated asset bundle system to use modern Odoo 18 syntax
- Improved error handling in configuration parameters
- Added proper field descriptions for better user experience

### Migration Notes
- This version is compatible with Odoo 18.0
- No data migration required
- Configuration settings are preserved during upgrade
- Custom CSS and SCSS files remain unchanged