# Ghost API Branding & Design Settings Analysis

## Overview
This document summarizes the comprehensive branding and design settings available through the Ghost Admin API v5.0.

## Available Branding Categories

### 🏷️ Basic Identity
- **title**: Site title/name
- **description**: Site description/tagline  
- **logo**: Main site logo (URL)
- **icon**: Site icon/favicon (URL)
- **cover_image**: Site cover/hero image (URL)

### 🎨 Visual Design
- **accent_color**: Primary accent color (hex code)
- **brand_color**: Secondary brand color
- **active_theme**: Current theme name (read-only through settings)

### 🧭 Navigation & User Experience
- **navigation**: Primary navigation menu (JSON array)
- **secondary_navigation**: Secondary navigation (JSON array)
- **portal_button**: Enable/disable portal button
- **portal_button_style**: Portal button style (icon-and-text, icon-only, text-only)
- **portal_button_signup_text**: Custom signup button text
- **portal_button_icon**: Portal button icon choice

### 📱 Social Media Integration
- **facebook**: Facebook profile URL
- **twitter**: Twitter/X profile URL
- **instagram**: Instagram profile URL
- **linkedin**: LinkedIn profile URL

### 🔍 SEO & Social Sharing
- **meta_title**: Default meta title
- **meta_description**: Default meta description
- **og_image**: Open Graph image for social sharing
- **og_title**: Open Graph title
- **og_description**: Open Graph description
- **twitter_image**: Twitter Card image
- **twitter_title**: Twitter Card title
- **twitter_description**: Twitter Card description

### 👥 Portal & Membership
- **portal_plans**: Available subscription plans (array)
- **portal_products**: Available products (array)

### 🔧 Advanced Customization
- **codeinjection_head**: Custom HTML/CSS/JS for `<head>`
- **codeinjection_foot**: Custom HTML/CSS/JS for footer
- **custom_css**: Additional CSS styles

## API Access Levels

### ✅ Available via Admin API Settings Endpoint
- All branding settings listed above (27 total)
- Requires Ghost Admin API key with proper permissions
- Endpoint: `/ghost/api/admin/settings/`

### ❌ Limited Access
- **Theme details**: Requires higher privileges (403 error)
- **Theme templates**: Not accessible via standard API key
- **Theme configurations**: Limited access

### ✅ Site Information Available
- **Ghost version**: Current Ghost installation version
- **Site URL**: Primary site URL
- **API version**: Available API versions

## Current Configuration Status (Example Site)

```
Total Ghost settings: 97
Branding-related settings: 27
Currently configured: 18
Configuration completeness: 66.7%
```

### Well Configured ✅
- Basic identity (title, logo, description, icon, cover)
- Accent color
- Navigation menus
- Portal/membership settings

### Needs Attention ⚠️
- Social media links (0/4 configured)
- SEO metadata (partial configuration)
- Custom CSS/code injection (minimal usage)

## Usage in Newsletter Script

### Current Implementation
The newsletter script uses these branding settings:
- Site title for newsletter headers
- Logo for email branding
- Description for footer content
- Accent color for design consistency

### Enhancement Opportunities
1. **Dynamic theme colors**: Use accent_color in email templates
2. **Social media integration**: Include social links in newsletter footer
3. **Brand consistency**: Use logo and cover images in email design
4. **SEO optimization**: Leverage meta descriptions for newsletter previews

## API Methods Added

### `get_comprehensive_branding_settings()`
- Fetches all branding-related settings
- Categorizes settings by type
- Provides detailed analysis and summary

### `get_theme_information()`
- Attempts to fetch theme details
- Retrieves site information
- Shows Ghost version and configuration

### `analyze_branding_capabilities()`
- Comprehensive analysis of branding setup
- Configuration completeness assessment
- Actionable recommendations

## Command Line Tools

```bash
# Check basic branding settings
python3 ghost.py --check-branding

# Check theme information
python3 ghost.py --check-theme

# Comprehensive branding analysis
python3 ghost.py --analyze-branding
```

## Recommendations

### For Newsletter Enhancement
1. **Color consistency**: Use `accent_color` in email templates
2. **Brand identity**: Include `logo` in email headers
3. **Social engagement**: Add social media links from settings
4. **Professional appearance**: Use `cover_image` for newsletter headers

### For Site Configuration
1. **Complete SEO setup**: Add meta_title and meta_description
2. **Social media**: Configure social platform URLs
3. **Brand colors**: Set brand_color for additional theming options
4. **Custom styling**: Use codeinjection_head for additional branding

## Technical Notes

- API Version: v5.0 required for full feature access
- Authentication: JWT token required for Admin API access
- Rate limiting: Standard Ghost API rate limits apply
- Permissions: Admin API key needed (Content API has limited access)

## Conclusion

The Ghost API provides comprehensive branding and design settings that can significantly enhance newsletter customization and brand consistency. While some advanced theme settings require higher privileges, the available settings offer substantial opportunities for branding integration.
