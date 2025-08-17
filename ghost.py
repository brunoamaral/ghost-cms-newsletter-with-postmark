#!/usr/bin/env python3

from bs4 import BeautifulSoup
import argparse
import datetime
import jwt
import os
import requests
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GhostNewsletterSender:
    def __init__(self):
        # Load environment variables with explicit path
        script_dir = os.path.dirname(os.path.realpath(__file__))
        env_path = os.path.join(script_dir, '.env')
        load_dotenv(env_path)
        
        # Ghost API settings
        self.ghost_admin_api_key = os.getenv('GHOST_ADMIN_API_KEY')
        self.ghost_content_api_key = os.getenv('GHOST_CONTENT_API_KEY')
        self.ghost_admin_url = os.getenv('GHOST_ADMIN_URL')
        self.ghost_website_url = os.getenv('GHOST_WEBSITE_URL')
        self.ghost_test_email = os.getenv('GHOST_TEST_EMAIL')
        
        # Postmark API settings
        self.postmark_server_token = os.getenv('POSTMARK_SERVER_TOKEN')
        self.from_name = os.getenv('FROM_NAME')
        self.from_email = os.getenv('FROM_EMAIL', 'subscriptions@brunoamaral.eu')
        self.message_stream = os.getenv('POSTMARK_MESSAGE_STREAM', 'broadcast')
        
        # Check if we're in Postmark test mode
        self.is_postmark_test_mode = self.postmark_server_token == 'POSTMARK_API_TEST'
        if self.is_postmark_test_mode:
            print("🧪 Running in Postmark TEST mode - emails will not be delivered")
        
        # Other settings
        self.website_domain = os.getenv('WEBSITE_DOMAIN')
        
        # Validate required environment variables
        required_vars = [
            'GHOST_ADMIN_API_KEY', 'GHOST_ADMIN_URL', 'GHOST_WEBSITE_URL',
            'POSTMARK_SERVER_TOKEN', 'FROM_NAME', 'FROM_EMAIL'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def generate_ghost_jwt(self):
        """Generate JWT token for Ghost Admin API authentication"""
        try:
            # Split the API key into ID and SECRET
            key_id, key_secret = self.ghost_admin_api_key.split(':')
            
            # Convert hex secret to bytes
            key_secret_bytes = bytes.fromhex(key_secret)
            
            # Create JWT payload
            now = int(time.time())
            payload = {
                'iat': now,
                'exp': now + 300,  # 5 minutes from now
                'aud': '/admin/'
            }
            
            # Create JWT header
            header = {
                'alg': 'HS256',
                'typ': 'JWT',
                'kid': key_id
            }
            
            # Generate JWT token
            token = jwt.encode(payload, key_secret_bytes, algorithm='HS256', headers=header)
            return token
            
        except Exception as e:
            print(f"Error generating JWT token: {e}")
            return None

    def get_ghost_members(self):
        """Fetch active members from Ghost Admin API"""
        try:
            token = self.generate_ghost_jwt()
            if not token:
                return []
            
            headers = {
                'Authorization': f'Ghost {token}',
                'Content-Type': 'application/json',
                'Accept-Version': 'v5.0'
            }
            
            # Fetch all members with pagination
            members = []
            page = 1
            limit = 100
            
            while True:
                url = f"{self.ghost_admin_url}/ghost/api/admin/members/"
                params = {
                    'limit': limit,
                    'page': page,
                    'filter': 'subscribed:true'  # Only get subscribed members
                }
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    print(f"Error fetching members: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                members.extend(data.get('members', []))
                
                # Check if there are more pages
                pagination = data.get('meta', {}).get('pagination', {})
                if pagination.get('pages', 1) <= page:
                    break
                
                page += 1
            
            # Extract email addresses
            email_addresses = [member['email'] for member in members if member.get('email')]
            print(f"Found {len(email_addresses)} subscribed members")
            
            return email_addresses
            
        except Exception as e:
            print(f"Error fetching Ghost members: {e}")
            return []

    def get_latest_post_from_ghost(self):
        """Fetch the latest post from Ghost Content API"""
        try:
            if not self.ghost_content_api_key:
                print("Ghost Content API key not found")
                return None
            
            # Build the API URL
            base_url = self.ghost_admin_url.replace('/ghost/api/admin', '')
            url = f"{base_url}/ghost/api/content/posts/"
            
            headers = {
                'Accept-Version': 'v5.0'
            }
            
            params = {
                'key': self.ghost_content_api_key,
                'limit': 1,
                'order': 'published_at desc',
                'include': 'tags,authors',
                'formats': 'html'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching post from Ghost API: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            posts = data.get('posts', [])
            
            if not posts:
                print("No posts found in Ghost")
                return None
            
            post = posts[0]
            print(f"Found post from Ghost: {post.get('title', 'Untitled')}")
            
            return post
            
        except Exception as e:
            print(f"Error fetching post from Ghost API: {e}")
            return None

    def load_template(self):
        """Load and return the HTML email template"""
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            template_path = os.path.join(script_dir, 'templates', 'ghost', 'newsletter.html')
            
            with open(template_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        except Exception as e:
            print(f"Error loading template: {e}")
            return None

    def process_content(self, content):
        """Process HTML content for email compatibility"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Style paragraphs
            p_style = "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: normal; margin: 0 0 16px 0; line-height: 1.6; color: #495057;"
            
            for p_tag in soup.find_all('p'):
                p_tag['style'] = p_style
            
            # Style images
            for img_tag in soup.find_all('img'):
                img_tag['style'] = "width: 100%; height: auto; border-radius: 4px; margin: 16px 0;"
                img_tag.attrs.pop('width', None)
                img_tag.attrs.pop('height', None)
            
            # Style headings
            for i, h_tag in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                font_size = 28 - (i * 2)  # Decreasing font sizes
                h_style = f"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: {font_size}px; font-weight: 700; margin: 24px 0 16px 0; line-height: 1.3; color: #2c3e50;"
                
                for heading in soup.find_all(h_tag):
                    heading['style'] = h_style
            
            # Style links
            for a_tag in soup.find_all('a'):
                a_tag['style'] = "color: #007bff; text-decoration: none; font-weight: 500;"
            
            # Return the inner HTML content without wrapping tags
            if soup.body:
                return str(soup.body.decode_contents())
            else:
                return str(soup)
            
        except Exception as e:
            print(f"Error processing content: {e}")
            return content

    def add_utm_tags(self, content, post_url):
        """Add UTM tracking tags to all links"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Generate UTM tags
            now = datetime.datetime.now()
            week_number = now.strftime("%U")
            year = now.strftime("%y")
            utm_tags = f"?utm_source={self.website_domain}&utm_medium=email&utm_campaign=newsletter-{year}{week_number}"
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # Skip if it's already a full URL from a different domain
                if href.startswith('http') and self.website_domain not in href:
                    continue
                
                # Add UTM tags
                if "?" in href:
                    href += "&" + utm_tags.lstrip('?')
                elif "#" in href:
                    href_parts = href.split("#", 1)
                    href = href_parts[0] + utm_tags + "#" + href_parts[1]
                else:
                    href += utm_tags
                
                a_tag['href'] = href
            
            return str(soup)
            
        except Exception as e:
            print(f"Error adding UTM tags: {e}")
            return content

    def generate_unsubscribe_link(self, email):
        """Generate unsubscribe link for the email using Ghost portal"""
        try:
            # Use Ghost's built-in portal unsubscribe system
            return f'{self.ghost_website_url}/#/portal/account/newsletters'
        except Exception as e:
            print(f"Error generating unsubscribe link: {e}")
            return f'{self.ghost_website_url}/#/portal/account/newsletters'

    def render_template(self, template, post):
        """Render the email template with post data"""
        try:
            # Handle Ghost API post object
            post_content = post.get('html', '')
            post_title = post.get('title', 'Untitled')
            post_url = post.get('url', '')
            post_excerpt = post.get('excerpt', '')
            featured_image = post.get('feature_image', '')
            published_at = post.get('published_at', '')
            
            # Build full URL if needed
            if post_url and not post_url.startswith('http'):
                post_url = f"{self.ghost_website_url}{post_url}"
            
            # Format published date
            if published_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%B %d, %Y")
                except:
                    formatted_date = datetime.datetime.now().strftime("%B %d, %Y")
            else:
                formatted_date = datetime.datetime.now().strftime("%B %d, %Y")
            
            # Process content
            processed_content = self.process_content(post_content)
            processed_content = self.add_utm_tags(processed_content, post_url)
            
            # Template variables
            template_vars = {
                'newsletter_title': f"{self.from_name}'s Newsletter",
                'post_excerpt': post_excerpt[:150] + '...' if len(post_excerpt) > 150 else post_excerpt,
                'author_name': self.from_name,
                'newsletter_name': 'Weekly Notes',
                'publish_date': formatted_date,
                'post_url': post_url,
                'featured_image': featured_image,
                'post_title': post_title,
                'post_content': processed_content,
                'website_url': self.ghost_website_url,
                'footer_address': os.getenv('GHOST_NEWSLETTER_ADDRESS', f'{self.from_name}'),
                'unsubscribe_url': '{{unsubscribe_url}}'  # Will be replaced per email
            }
            
            # Replace template variables
            rendered = template
            for key, value in template_vars.items():
                if key == 'post_content':
                    # Handle triple braces for raw HTML content
                    placeholder = '{{{' + key + '}}}'
                    rendered = rendered.replace(placeholder, str(value) if value else '')
                else:
                    # Handle double braces for escaped content
                    placeholder = '{{' + key + '}}'
                    rendered = rendered.replace(placeholder, str(value) if value else '')
            
            # Handle conditional featured image
            if template_vars['featured_image']:
                # If there's a featured image, just remove the conditional tags
                rendered = rendered.replace('{{#if featured_image}}', '').replace('{{/if}}', '')
            else:
                # If no featured image, remove the entire section
                import re
                # Remove everything between {{#if featured_image}} and {{/if}} including the tags
                pattern = r'{{#if featured_image}}.*?{{/if}}'
                rendered = re.sub(pattern, '', rendered, flags=re.DOTALL)
            
            return rendered
            
        except Exception as e:
            print(f"Error rendering template: {e}")
            return None

    def send_email(self, to_addr, content, subject):
        """Send email using Postmark API"""
        try:
            # Prepare Postmark API request
            url = "https://api.postmarkapp.com/email"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.postmark_server_token
            }
            
            # Format the From field with name (following Postmark format)
            from_addr = f'"{self.from_name}" <{self.from_email}>' if self.from_name else self.from_email
            
            payload = {
                "From": from_addr,
                "To": to_addr,
                "Subject": subject,
                "HtmlBody": content,
                "MessageStream": self.message_stream
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                # Parse response to get MessageID for logging
                try:
                    response_data = response.json()
                    message_id = response_data.get('MessageID', 'Unknown')
                    if self.is_postmark_test_mode:
                        print(f"🧪 Test email processed for {to_addr} (MessageID: {message_id})")
                    else:
                        print(f"Email sent successfully to {to_addr} (MessageID: {message_id})")
                except:
                    if self.is_postmark_test_mode:
                        print(f"🧪 Test email processed for {to_addr}")
                    else:
                        print(f"Email sent successfully to {to_addr}")
                return True
            elif response.status_code == 401:
                print(f"Postmark authentication failed. Check your server token.")
                return False
            elif response.status_code == 422:
                print(f"Invalid email data for {to_addr}: {response.text}")
                return False
            else:
                print(f"Postmark API error {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            print(f"Failed to send email to {to_addr}. Error: {e}")
            return False

    def send_newsletter(self, dry_run=True):
        """Main function to send newsletter"""
        try:
            print("🚀 Starting Ghost newsletter sender...")
            
            # Get latest post
            print("📰 Fetching latest post...")
            latest_post = self.get_latest_post_from_ghost()
            if not latest_post:
                print("No post found. Exiting.")
                return False
            
            # Get post title for display
            post_title = latest_post.get('title', 'Untitled')
            
            print(f"Found post: {post_title}")
            
            # Load template
            print("📧 Loading email template...")
            template = self.load_template()
            if not template:
                print("Failed to load template. Exiting.")
                return False
            
            # Render template
            print("🎨 Rendering email content...")
            email_content = self.render_template(template, latest_post)
            if not email_content:
                print("Failed to render template. Exiting.")
                return False
            
            # Get subscribers
            print("👥 Fetching subscribers from Ghost...")
            if dry_run:
                print("🧪 DRY RUN MODE - Using test email")
                test_email = self.ghost_test_email or self.from_email
                email_addresses = [test_email]
            else:
                email_addresses = self.get_ghost_members()
                
            if not email_addresses:
                print("No subscribers found. Exiting.")
                return False
            
            print(f"📬 Sending to {len(email_addresses)} recipients...")
            
            # Send emails
            sent_count = 0
            failed_count = 0
            
            for email_addr in email_addresses:
                try:
                    # Generate personalized unsubscribe link
                    unsubscribe_link = self.generate_unsubscribe_link(email_addr)
                    personal_content = email_content.replace('{{unsubscribe_url}}', unsubscribe_link)
                    
                    # Send email
                    email_subject = post_title
                    if self.send_email(email_addr, personal_content, email_subject):
                        sent_count += 1
                        print(f"Sent to {email_addr}")
                    else:
                        failed_count += 1
                        print(f"Failed to send to {email_addr}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"Error sending to {email_addr}: {e}")
            
            print(f"📊 Newsletter sending complete:")
            print(f"   Sent: {sent_count}")
            print(f"   Failed: {failed_count}")
            print(f"   📝 Subject: {post_title}")
            
            return sent_count > 0
            
        except Exception as e:
            print(f"Error in send_newsletter: {e}")
            return False


def main():
    """Main function"""
    try:
        # Setup argument parser
        parser = argparse.ArgumentParser(description='Send newsletter using Ghost API.')
        parser.add_argument('--send', action='store_true', help='Send to all subscribers (default is dry run)')
        
        args = parser.parse_args()
        
        # Create newsletter sender
        sender = GhostNewsletterSender()
        
        # Send newsletter
        success = sender.send_newsletter(dry_run=not args.send)
        
        if success:
            print("🎉 Newsletter sent successfully!")
            sys.exit(0)
        else:
            print("💥 Newsletter sending failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
