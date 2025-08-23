# Missing Newsletter Settings Analysis

## Email/Newsletter Settings Available but Not Currently Used

Based on the Ghost API analysis, here are the valuable newsletter settings we're not currently utilizing in our template:

### 📧 **Core Email Settings**
- `email_track_opens`: True (for analytics)
- `email_track_clicks`: True (for engagement tracking)
- `default_email_address`: bruno@brunoamaral.eu
- `support_email_address`: subscriptions@brunoamaral.eu

### 📰 **Newsletter Design & Configuration**
From the active newsletter "Bruno Amaral":

#### **Header & Branding**
- `header_image`: https://brunoamaral.eu/content/images/2025/08/IMG_8250-4.jpeg
- `sender_name`: Bruno Amaral
- `sender_email`: subscriptions@brunoamaral.eu
- `sender_reply_to`: mail@brunoamaral.eu
- `show_header_icon`: True
- `show_header_title`: True
- `show_header_name`: False

#### **Typography & Layout**
- `title_font_category`: sans_serif
- `body_font_category`: sans_serif
- `title_alignment`: center
- `background_color`: light

#### **Content Display Options**
- `show_feature_image`: True
- `show_excerpt`: True
- `show_author`: None
- `show_post_title_section`: True
- `show_comment_cta`: True
- `show_subscription_details`: True
- `show_latest_posts`: True
- `show_badge`: True

#### **Footer & Branding**
- `footer_content`: None (could be customized)
- `subject_prefix`: None (could add newsletter branding)

### 🎨 **Additional Branding Settings**
- `heading_font`: Could be used for consistent typography
- `body_font`: Could be used for consistent typography
- `portal_button_signup_text`: "Subscribe" (for CTA buttons)
- `portal_button_style`: icon-and-text

## Recommendations for Template Enhancement

### 1. **Header Customization**
- Use `header_image` for newsletter header
- Implement `show_header_icon` and `show_header_title` settings
- Use `sender_name` for consistent branding

### 2. **Typography Integration**
- Apply `title_font_category` and `body_font_category` to email styles
- Use `title_alignment` for header alignment
- Consider `heading_font` and `body_font` for consistent typography

### 3. **Content Presentation**
- Implement `show_feature_image` setting for post images
- Use `show_excerpt` to control excerpt display
- Apply `show_author` setting if author attribution is desired

### 4. **Email Functionality**
- Leverage `email_track_opens` and `email_track_clicks` for analytics
- Use proper sender information from newsletter settings
- Implement `support_email_address` for unsubscribe/support links

### 5. **Background & Colors**
- Use `background_color` setting (currently "light")
- Could implement additional color settings if available

### 6. **Footer Enhancement**
- Add custom `footer_content` if configured
- Include subscription management links using `show_subscription_details`
- Add support contact using `support_email_address`

## Implementation Priority

**High Priority:**
1. Header image and branding
2. Typography settings
3. Sender information
4. Content display options

**Medium Priority:**
1. Footer customization
2. Email tracking settings
3. Background color settings

**Low Priority:**
1. Advanced layout options
2. Additional design customizations
