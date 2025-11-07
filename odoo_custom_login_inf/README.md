# Odoo Custom Login Interface - Skan Portal Edition

## Overview
This module provides a customized login page with Egyptian Real Estate Platform branding and design, matching the skan portal UI aesthetic. It includes **forced redirect** functionality for portal users.

## Features
- **Skan Portal Design**: Login page styled to match the Egyptian Real Estate Platform portal
- **Modern UI**: Clean, professional design with Egyptian government color scheme
- **Responsive Layout**: Works perfectly across all device sizes
- **Brand Consistency**: Unified navbar and footer matching portal templates
- **Font Awesome Icons**: Enhanced visual appeal with icon integration
- **Egyptian Fonts**: Uses Cairo and Roboto font families for authentic look
- **Forced Portal Redirect**: Portal users are automatically redirected to configured path (ignores URL parameters)
- **Reset Password**: Custom password reset pages matching login design and branding

## Portal Redirect Behavior
- **Portal Users**: ALWAYS redirected to the "Portal Redirect Path" setting (configured in Settings)
  - Cannot bypass this redirect using URL parameters
  - Default: `/my`
  - Configurable to any custom path (e.g., `/unit-reservation`, `/portal/home`, etc.)
  
- **Internal Users**: Can use redirect parameters normally
  - Default: `/web`
  - URL redirect parameters are honored

## Design Elements
- **Primary Colors**: Egyptian Red (#C62E29) with gradient effects
- **Typography**: Cairo and Roboto font families
- **Layout**: Centered login card with header, form, and footer sections
- **Navbar**: Matching skan portal navbar with logo and branding
- **Footer**: Consistent footer design across all pages

## Installation
1. Copy this module to your Odoo addons directory
2. Update your addons list
3. Install the module from Apps menu
4. The login page will automatically use the new design

## Configuration
### Portal Redirect Path
1. Go to **Settings > General Settings**
2. Scroll down to **Login Background** section
3. Set **Portal Redirect Path** to your desired URL (e.g., `/unit-reservation`)
4. Click **Save**

**Important**: Portal users will be FORCED to this path after login, regardless of any redirect parameters in the URL.

### Login Background (Optional)
You can also configure:
- **Style**: Default, Left, Right, or Middle layout
- **Background Type**: Image, Color, or Gradient
- Additional background customization options

### Reset Password Feature
The module automatically includes:
- **Custom Reset Password Page**: Matches login page design
- **Branded Email Forms**: Consistent skan portal styling
- **User-Friendly Interface**: Clear instructions and feedback
- **Responsive Design**: Works on all devices

## Customization
The login template includes:
- Bootstrap 5.1.3 for responsive design
- Font Awesome 4.7 for icons
- Egyptian government fonts (Cairo, Roboto)
- Custom CSS matching skan portal design variables

## Version Compatibility
- **Current Version**: 18.0.1.2.0
- **Odoo Version**: 18.0
- **Python Version**: 3.8+
- **Integrated with**: skan module (Egyptian Real Estate Platform)

## Technical Details
- Uses QWeb templates for login layout
- Inherits from web.layout base template
- Custom CSS with CSS variables for easy theming
- Supports multi-database environments
- Password reset functionality enabled
- Controller override for forced portal redirect

## License
LGPL-3

## Support
For support and questions, contact: webdeveloper.inf@gmail.com

## Author
NxonBytes (Modified for Skan Portal by Ahmed Shawky)
