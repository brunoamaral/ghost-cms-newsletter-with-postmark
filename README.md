# Ghost Newsletter Sender

## Motivation

The self-hosted Ghost CMS requires a Mailgun account to send bulk emails but that may not be an option for everyone.

This script uses the Ghost API to send newsletters using the Postmark API. 
It's not as good as using Ghost to send the directly, but I hope it can help others wanting to use Ghost.

## What it does

This script uses the Ghost CMS and Postmark APIs to fetch the latest blog post, formats it into an email, and sends it to all subscribed members.

## Usage

1. Edit the `.env` file following the example, and optionally: Edit the html template located at `templates/ghost/newsletter.html`.
2. Run `python ghost.py`. You may want to automate it to run at every new post, but that would require some way to track new posts.

### Basic Commands

```bash
# Dry run (sends test email only)
python3 ghost.py

# Send to all subscribers
python3 ghost.py --send

# View help
python3 ghost.py --help
```

Features:
- Fetch the latest post from your Ghost CMS
- Generate a newsletter email template
- Send newsletters to all Ghost subscribers
- Handle unsubscribe links through Ghost's portal system
- Add UTM tracking to all links for analytics

## Caveats

1. I have only tested this with a single newsletter configured on Ghost. Support for multiple newsletters may require additional development.
2. There is no support for free / paid tiers from Ghost. 
3. The template only supports one blog post.

## File Structure

```
scripts/
├── ghost.py                           # Main newsletter sender script
├── requirements-ghost.txt             # Python dependencies
├── .env                              # Environment variables (create from .env.example)
├── templates/
│   └── ghost/
│       └── newsletter.html           # Email template with modern design
└── README.md                         # This documentation
```

### File Descriptions

- **`ghost.py`** - The main Python script that handles Ghost API integration, email rendering, and newsletter sending
- **`requirements-ghost.txt`** - Lists all Python package dependencies needed to run the script
- **`.env`** - Contains sensitive configuration data (API keys, email credentials, etc.)
- **`templates/ghost/newsletter.html`** - Modern, responsive email template with inline CSS for email client compatibility

## Prerequisites

- Python 3.7 or higher
- Ghost CMS instance with Admin and Content API access
- Postmark email service account with verified sender domain

## Detailled Setup

### 1. Install Dependencies

```bash
pip install -r requirements-ghost.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the same directory as `ghost.py`:

```bash
# Ghost API Configuration
GHOST_ADMIN_API_KEY=your_admin_api_key_here
GHOST_CONTENT_API_KEY=your_content_api_key_here
GHOST_ADMIN_URL=https://your-ghost-admin.com/ghost/api/admin
GHOST_WEBSITE_URL=https://your-website.com
GHOST_TEST_EMAIL=your-test-email@example.com
GHOST_NEWSLETTER_ADDRESS="Your Name, Your Address, City, Country"

# Email Server Configuration
POSTMARK_SERVER_TOKEN=your_postmark_server_token_here
POSTMARK_MESSAGE_STREAM=broadcast
FROM_NAME=Your Name
FROM_EMAIL=your-verified-sender@yourdomain.com

# Website Configuration
WEBSITE_DOMAIN=your-website.com
```

### 3. Ghost API Keys Setup

#### Admin API Key
1. Go to your Ghost Admin panel
2. Navigate to **Integrations** → **Custom Integrations**
3. Click **Add custom integration**
4. Copy the **Admin API Key**

#### Content API Key
1. In the same integration settings
2. Copy the **Content API Key**

### 4. Postmark Setup

#### Getting Your Server Token
1. Sign up for a [Postmark account](https://postmarkapp.com)
2. Create a new server or use an existing one
3. Go to **Settings** → **API Tokens**
4. Copy your **Server API Token**

#### Verify Your Sender Domain
1. Go to **Senders** → **Sender Signatures** 
2. Add and verify your sender email domain
3. Ensure the email in `FROM_EMAIL` is verified

#### Testing
- Use `POSTMARK_API_TEST` as your server token for testing
- Test emails won't be delivered but will validate your setup

### 5. Email Template

The script uses `templates/ghost/newsletter.html` which includes:
- Responsive design for mobile and desktop
- Professional typography and spacing
- Conditional featured image display
- Modern styling with inline CSS
- Ghost portal integration for unsubscribe

### Workflow

1. **Dry Run First**: Always test with `python3 ghost.py` to send to your test email
2. **Review Email**: Check formatting, content, and links in the test email
3. **Send to All**: Use `python3 ghost.py --send` to send to all subscribers

## Configuration Options

### Environment Variables Explained

| Variable | Purpose | Example |
|----------|---------|---------|
| `GHOST_ADMIN_API_KEY` | Authentication for Ghost Admin API | `key_id:secret_hex` |
| `GHOST_CONTENT_API_KEY` | Authentication for Ghost Content API | `abc123...` |
| `GHOST_ADMIN_URL` | URL to your Ghost admin API endpoint | `https://admin.example.com/ghost/api/admin` |
| `GHOST_WEBSITE_URL` | Your public website URL | `https://example.com` |
| `GHOST_TEST_EMAIL` | Email address for dry run testing | `test@example.com` |
| `GHOST_NEWSLETTER_ADDRESS` | Footer address for newsletters | `"John Doe, 123 Main St, City, Country"` |
| `POSTMARK_SERVER_TOKEN` | Postmark API server token | `abc123-def456-...` |
| `POSTMARK_MESSAGE_STREAM` | Postmark message stream | `broadcast` |
| `FROM_NAME` | Newsletter sender name | `John Doe` |
| `FROM_EMAIL` | Verified sender email address | `newsletter@example.com` |
| `WEBSITE_DOMAIN` | Domain for UTM tracking | `example.com` |

## Template Customization

The email template (`templates/ghost/newsletter.html`) supports these variables:

- `{{newsletter_title}}` - Newsletter title
- `{{author_name}}` - Author/sender name
- `{{newsletter_name}}` - Newsletter name ("Weekly Notes")
- `{{publish_date}}` - Formatted publication date
- `{{post_title}}` - Blog post title
- `{{{post_content}}}` - Blog post HTML content (triple braces for raw HTML)
- `{{post_url}}` - Link to full blog post
- `{{featured_image}}` - Featured image URL
- `{{website_url}}` - Your website URL
- `{{footer_address}}` - Newsletter footer address
- `{{unsubscribe_url}}` - Ghost portal unsubscribe link

## Analytics

The script automatically adds UTM parameters to all links:
- `utm_source`: Your website domain
- `utm_medium`: email  
- `utm_campaign`: newsletter-{year}{week_number}

Track these in Google Analytics or your preferred analytics platform.

---

— [Bruno Amaral](https://brunoamaral.eu)