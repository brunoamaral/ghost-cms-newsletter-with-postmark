#!/usr/bin/env python3

from bs4 import BeautifulSoup
import argparse
import datetime
import jwt
import os
import requests
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GhostNewsletterSender:
    def __init__(self, max_posts=5, days_back=30, newsletter_interval='weekly', 
                 filter_tags=None, featured_only=False, auto_interval=False):
        # Newsletter configuration
        self.max_posts = max_posts
        self.days_back = days_back
        self.newsletter_interval = newsletter_interval
        self.filter_tags = filter_tags or []
        self.featured_only = featured_only
        self.auto_interval = auto_interval
        
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

    def get_blog_settings_from_ghost(self):
        """Fetch blog settings from Ghost Admin API"""
        try:
            token = self.generate_ghost_jwt()
            if not token:
                return {}
            
            headers = {
                'Authorization': f'Ghost {token}',
                'Content-Type': 'application/json',
                'Accept-Version': 'v5.0'
            }
            
            url = f"{self.ghost_admin_url}/ghost/api/admin/settings/"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Warning: Could not fetch blog settings: {response.status_code}")
                return {}
            
            settings_data = response.json()
            settings = settings_data.get('settings', [])
            
            # Extract relevant settings
            blog_settings = {}
            for setting in settings:
                key = setting.get('key')
                if key in ['title', 'description', 'logo', 'icon', 'cover_image']:
                    blog_settings[key] = setting.get('value')
            
            print(f"Fetched blog settings: title='{blog_settings.get('title')}', logo={bool(blog_settings.get('logo'))}")
            return blog_settings
            
        except Exception as e:
            print(f"Warning: Error fetching blog settings: {e}")
            return {}

    def get_comprehensive_branding_settings(self):
        """Fetch comprehensive branding and design settings from Ghost API"""
        try:
            token = self.generate_ghost_jwt()
            if not token:
                print("❌ Could not generate JWT token")
                return None
            
            headers = {
                'Authorization': f'Ghost {token}',
                'Content-Type': 'application/json',
                'Accept-Version': 'v5.0'
            }
            
            # Fetch all settings
            print("🔍 Fetching all Ghost settings...")
            url = f"{self.ghost_admin_url}/ghost/api/admin/settings/"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Could not fetch settings: {response.status_code} - {response.text}")
                return None
            
            settings_data = response.json()
            all_settings = settings_data.get('settings', [])
            
            # Categorize settings related to branding and design
            branding_keys = [
                # Basic branding
                'title', 'description', 'logo', 'icon', 'cover_image',
                # Brand colors and design
                'accent_color', 'brand_color', 'brand', 'brand_primary_color',
                # Navigation and appearance
                'navigation', 'secondary_navigation', 'header_style',
                # Social media
                'facebook', 'twitter', 'linkedin', 'instagram', 'youtube',
                'social_accounts', 'twitter_url', 'facebook_url',
                # Meta and SEO
                'meta_title', 'meta_description', 'og_image', 'og_title', 'og_description',
                'twitter_image', 'twitter_title', 'twitter_description',
                # Ghost-specific design
                'theme', 'theme_config', 'custom_theme_settings',
                # Portal/membership styling
                'portal_button', 'portal_button_style', 'portal_button_signup_text',
                'portal_button_icon', 'portal_plans', 'portal_products',
                # Email branding
                'email_header_image', 'email_footer', 'email_design',
                # Site-wide settings
                'site_language', 'timezone', 'default_locale',
                # Custom settings
                'codeinjection_head', 'codeinjection_foot', 'custom_css'
            ]
            
            # Extract all settings and categorize them
            branding_settings = {}
            other_settings = {}
            
            for setting in all_settings:
                key = setting.get('key')
                value = setting.get('value')
                
                if key in branding_keys:
                    branding_settings[key] = value
                else:
                    other_settings[key] = value
            
            # Print organized results
            print("\n🎨 BRANDING & DESIGN SETTINGS FOUND:")
            print("=" * 50)
            
            categories = {
                'Basic Branding': ['title', 'description', 'logo', 'icon', 'cover_image'],
                'Colors & Theme': ['accent_color', 'brand_color', 'brand', 'brand_primary_color', 'theme', 'theme_config'],
                'Navigation': ['navigation', 'secondary_navigation', 'header_style'],
                'Social Media': ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'social_accounts', 'twitter_url', 'facebook_url'],
                'SEO & Meta': ['meta_title', 'meta_description', 'og_image', 'og_title', 'og_description', 'twitter_image', 'twitter_title', 'twitter_description'],
                'Portal/Membership': ['portal_button', 'portal_button_style', 'portal_button_signup_text', 'portal_button_icon', 'portal_plans', 'portal_products'],
                'Email Design': ['email_header_image', 'email_footer', 'email_design'],
                'Customization': ['codeinjection_head', 'codeinjection_foot', 'custom_css', 'custom_theme_settings']
            }
            
            for category, keys in categories.items():
                category_settings = {k: branding_settings.get(k) for k in keys if k in branding_settings}
                if category_settings:
                    print(f"\n📂 {category}:")
                    for key, value in category_settings.items():
                        if value:
                            if isinstance(value, str) and len(value) > 100:
                                print(f"  • {key}: {value[:97]}...")
                            else:
                                print(f"  • {key}: {value}")
                        else:
                            print(f"  • {key}: (empty)")
            
            print(f"\n📊 SUMMARY:")
            print(f"  • Total settings found: {len(all_settings)}")
            print(f"  • Branding-related settings: {len(branding_settings)}")
            print(f"  • Settings with values: {len([k for k, v in branding_settings.items() if v])}")
            
            # Also check if there are any other potentially relevant settings
            potential_branding = [k for k in other_settings.keys() if any(word in k.lower() for word in ['color', 'style', 'design', 'brand', 'theme', 'css', 'image', 'logo', 'icon'])]
            if potential_branding:
                print(f"\n🔍 OTHER POTENTIALLY RELEVANT SETTINGS:")
                for key in potential_branding[:10]:  # Show first 10
                    value = other_settings[key]
                    if isinstance(value, str) and len(value) > 50:
                        print(f"  • {key}: {value[:47]}...")
                    else:
                        print(f"  • {key}: {value}")
                if len(potential_branding) > 10:
                    print(f"  ... and {len(potential_branding) - 10} more")
            
            return {
                'branding_settings': branding_settings,
                'all_settings': {s.get('key'): s.get('value') for s in all_settings},
                'total_count': len(all_settings)
            }
            
        except Exception as e:
            print(f"❌ Error fetching comprehensive branding settings: {e}")
            return None

    def get_newsletter_settings(self):
        """Fetch newsletter-specific configuration from Ghost API"""
        try:
            token = self.generate_ghost_jwt()
            if not token:
                print("❌ Could not generate JWT token")
                return None
            
            headers = {
                'Authorization': f'Ghost {token}',
                'Content-Type': 'application/json',
                'Accept-Version': 'v5.0'
            }
            
            # Fetch newsletters
            print("📰 Fetching newsletter configuration...")
            newsletters_url = f"{self.ghost_admin_url}/ghost/api/admin/newsletters/"
            response = requests.get(newsletters_url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Could not fetch newsletters: {response.status_code}")
                return None
            
            newsletters_data = response.json()
            newsletters = newsletters_data.get('newsletters', [])
            
            # Find active newsletter
            active_newsletter = None
            for newsletter in newsletters:
                if newsletter.get('status') == 'active':
                    active_newsletter = newsletter
                    break
            
            if not active_newsletter:
                print("⚠️ No active newsletter found")
                return None
            
            # Also get email settings from site settings
            settings_url = f"{self.ghost_admin_url}/ghost/api/admin/settings/"
            settings_response = requests.get(settings_url, headers=headers)
            
            email_settings = {}
            if settings_response.status_code == 200:
                all_settings = settings_response.json().get('settings', [])
                email_keys = [
                    'email_track_opens', 'email_track_clicks', 'default_email_address',
                    'support_email_address', 'heading_font', 'body_font'
                ]
                for setting in all_settings:
                    if setting.get('key') in email_keys:
                        email_settings[setting.get('key')] = setting.get('value')
            
            return {
                'newsletter': active_newsletter,
                'email_settings': email_settings
            }
            
        except Exception as e:
            print(f"Error fetching newsletter settings: {e}")
            return None

    def get_theme_information(self):
        """Fetch theme-specific information from Ghost API"""
        try:
            token = self.generate_ghost_jwt()
            if not token:
                print("❌ Could not generate JWT token")
                return None
            
            headers = {
                'Authorization': f'Ghost {token}',
                'Content-Type': 'application/json',
                'Accept-Version': 'v5.0'
            }
            
            print("🎭 Fetching theme information...")
            
            # Try to fetch themes endpoint
            themes_url = f"{self.ghost_admin_url}/ghost/api/admin/themes/"
            themes_response = requests.get(themes_url, headers=headers)
            
            theme_info = {}
            
            if themes_response.status_code == 200:
                themes_data = themes_response.json()
                themes = themes_data.get('themes', [])
                
                print(f"\n🎭 THEMES INFORMATION:")
                print("=" * 40)
                print(f"Found {len(themes)} theme(s):")
                
                for theme in themes:
                    name = theme.get('name', 'Unknown')
                    active = theme.get('active', False)
                    version = theme.get('package', {}).get('version', 'Unknown')
                    status = "🟢 ACTIVE" if active else "⚪ Inactive"
                    
                    print(f"  • {name} (v{version}) {status}")
                    
                    if active:
                        theme_info['active_theme'] = {
                            'name': name,
                            'version': version,
                            'package': theme.get('package', {}),
                            'templates': theme.get('templates', [])
                        }
                        
                        # Show templates if available
                        templates = theme.get('templates', [])
                        if templates:
                            print(f"    Templates: {', '.join(templates[:5])}{'...' if len(templates) > 5 else ''}")
            else:
                print(f"⚠️  Could not fetch themes: {themes_response.status_code}")
            
            # Try to fetch site information
            site_url = f"{self.ghost_admin_url}/ghost/api/admin/site/"
            site_response = requests.get(site_url, headers=headers)
            
            if site_response.status_code == 200:
                site_data = site_response.json()
                site_info = site_data.get('site', {})
                
                print(f"\n🌐 SITE INFORMATION:")
                print("=" * 40)
                print(f"  • URL: {site_info.get('url', 'Unknown')}")
                print(f"  • Version: {site_info.get('version', 'Unknown')}")
                
                theme_info['site_info'] = site_info
            else:
                print(f"⚠️  Could not fetch site info: {site_response.status_code}")
                
            return theme_info
            
        except Exception as e:
            print(f"❌ Error fetching theme information: {e}")
            return None

    def analyze_branding_capabilities(self):
        """Analyze and summarize all available branding capabilities"""
        print("🎨 GHOST API BRANDING & DESIGN CAPABILITIES ANALYSIS")
        print("=" * 60)
        
        print("\n📋 WHAT THE GHOST API PROVIDES FOR BRANDING:")
        
        branding_data = self.get_comprehensive_branding_settings()
        if not branding_data:
            print("❌ Could not fetch branding data")
            return
            
        branding_settings = branding_data.get('branding_settings', {})
        
        # Analyze what's available vs what's configured
        capabilities = {
            '🏷️ Basic Identity': {
                'title': branding_settings.get('title'),
                'description': branding_settings.get('description'),
                'logo': branding_settings.get('logo'),
                'icon': branding_settings.get('icon'),
                'cover_image': branding_settings.get('cover_image')
            },
            '🎨 Visual Design': {
                'accent_color': branding_settings.get('accent_color'),
                'brand_color': branding_settings.get('brand_color'),
                'theme': branding_settings.get('active_theme', 'Not accessible via settings')
            },
            '🧭 Navigation & UX': {
                'navigation': branding_settings.get('navigation'),
                'secondary_navigation': branding_settings.get('secondary_navigation'),
                'portal_button_style': branding_settings.get('portal_button_style'),
                'portal_button_signup_text': branding_settings.get('portal_button_signup_text')
            },
            '📱 Social Media': {
                'facebook': branding_settings.get('facebook'),
                'twitter': branding_settings.get('twitter'),
                'instagram': branding_settings.get('instagram'),
                'linkedin': branding_settings.get('linkedin')
            },
            '🔍 SEO & Sharing': {
                'meta_title': branding_settings.get('meta_title'),
                'meta_description': branding_settings.get('meta_description'),
                'og_image': branding_settings.get('og_image'),
                'twitter_image': branding_settings.get('twitter_image')
            },
            '🔧 Customization': {
                'codeinjection_head': branding_settings.get('codeinjection_head'),
                'codeinjection_foot': branding_settings.get('codeinjection_foot'),
                'custom_css': branding_settings.get('custom_css')
            }
        }
        
        for category, items in capabilities.items():
            print(f"\n{category}:")
            configured_count = 0
            total_count = len(items)
            
            for key, value in items.items():
                status = "✅" if value else "⚪"
                if value and isinstance(value, str) and len(value) > 60:
                    value_display = value[:57] + "..."
                else:
                    value_display = value or "(not configured)"
                    
                print(f"  {status} {key}: {value_display}")
                if value:
                    configured_count += 1
            
            print(f"    → {configured_count}/{total_count} configured")
        
        # Theme information
        print(f"\n🎭 THEME INFORMATION:")
        theme_data = self.get_theme_information()
        if theme_data and 'site_info' in theme_data:
            site_info = theme_data['site_info']
            print(f"  • Ghost Version: {site_info.get('version', 'Unknown')}")
            print(f"  • Site URL: {site_info.get('url', 'Unknown')}")
            
        print(f"\n💡 SUMMARY:")
        total_settings = branding_data.get('total_count', 0)
        branding_count = len(branding_settings)
        configured_count = len([v for v in branding_settings.values() if v])
        
        print(f"  • Total Ghost settings: {total_settings}")
        print(f"  • Branding-related: {branding_count}")
        print(f"  • Currently configured: {configured_count}")
        print(f"  • Configuration completeness: {configured_count/branding_count*100:.1f}%")
        
        print(f"\n🚀 RECOMMENDATIONS FOR NEWSLETTER BRANDING:")
        print("  • ✅ Basic identity (title, logo, description) is well configured")
        if not branding_settings.get('accent_color'):
            print("  • ⚠️  Consider setting an accent color for brand consistency")
        if not branding_settings.get('meta_title'):
            print("  • ⚠️  Add meta title and description for better SEO")
        if not branding_settings.get('facebook') and not branding_settings.get('twitter'):
            print("  • ⚠️  Add social media links to increase engagement")
            
        return branding_data

    def detect_optimal_interval(self):
        """Auto-detect optimal newsletter interval based on posting frequency"""
        try:
            # Fetch posts from last 60 days to analyze frequency
            base_url = self.ghost_admin_url.replace('/ghost/api/admin', '')
            url = f"{base_url}/ghost/api/content/posts/"
            
            headers = {'Accept-Version': 'v5.0'}
            params = {
                'key': self.ghost_content_api_key,
                'limit': 20,
                'order': 'published_at desc',
                'filter': f'published_at:>={(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")}'
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                return self.days_back  # Fallback to default
            
            posts = response.json().get('posts', [])
            if len(posts) < 2:
                return self.days_back
            
            # Calculate average days between posts
            post_dates = [datetime.fromisoformat(post['published_at'].replace('Z', '+00:00')) for post in posts]
            intervals = [(post_dates[i] - post_dates[i+1]).days for i in range(len(post_dates)-1)]
            avg_interval = sum(intervals) / len(intervals)
            
            # Determine optimal newsletter frequency
            if avg_interval <= 2:  # Daily posting
                return 7  # Weekly newsletter
            elif avg_interval <= 7:  # Weekly posting
                return 14  # Bi-weekly newsletter
            else:  # Monthly or less
                return 30  # Monthly newsletter
                
        except Exception as e:
            print(f"Warning: Auto-interval detection failed: {e}")
            return self.days_back

    def filter_posts_by_criteria(self, posts):
        """Filter posts based on tags and featured status"""
        if not posts:
            return posts
        
        filtered_posts = []
        
        for post in posts:
            # Filter by featured status
            if self.featured_only and not post.get('featured', False):
                continue
            
            # Filter by tags
            if self.filter_tags:
                post_tags = [tag.get('name', '').lower() for tag in post.get('tags', [])]
                if not any(tag.lower() in post_tags for tag in self.filter_tags):
                    continue
            
            filtered_posts.append(post)
        
        return filtered_posts

    def enhance_post_images(self, posts):
        """Enhance post images with fallbacks and optimization"""
        for post in posts:
            feature_image = post.get('feature_image')
            
            if feature_image:
                # Add image optimization parameters for Ghost images
                if 'brunoamaral.eu' in feature_image or 'ghost' in feature_image.lower():
                    # Add Ghost image optimization
                    post['feature_image_optimized'] = f"{feature_image}?w=600&h=300&fit=crop"
                    post['feature_image_small'] = f"{feature_image}?w=300&h=150&fit=crop"
                else:
                    post['feature_image_optimized'] = feature_image
                    post['feature_image_small'] = feature_image
            else:
                # Use blog logo or default image as fallback
                blog_settings = self.get_blog_settings_from_ghost()
                post['feature_image_optimized'] = blog_settings.get('logo') or blog_settings.get('cover_image')
                post['feature_image_small'] = post['feature_image_optimized']
        
        return posts

    def generate_social_sharing_data(self, posts):
        """Generate social media sharing data for posts"""
        if not posts:
            return {}
        
        # Use featured post or first post for newsletter sharing
        featured_post = next((post for post in posts if post.get('featured')), posts[0])
        
        newsletter_title = f"{self.from_name} Newsletter - {featured_post.get('title', '')}"
        newsletter_url = f"{self.ghost_website_url}/newsletters" if self.ghost_website_url else ""
        
        return {
            'twitter_url': f"https://twitter.com/intent/tweet?text={newsletter_title}&url={newsletter_url}",
            'facebook_url': f"https://www.facebook.com/sharer/sharer.php?u={newsletter_url}",
            'linkedin_url': f"https://www.linkedin.com/sharing/share-offsite/?url={newsletter_url}",
            'newsletter_title': newsletter_title,
            'newsletter_url': newsletter_url
        }
    
    def generate_feedback_urls(self, post):
        """Generate feedback URLs for Ghost feedback system"""
        if not post:
            return {}
        
        post_id = post.get('id', 'default-post-id')
        post_slug = post.get('slug', 'default-slug')
        base_url = self.ghost_website_url or ""
        
        # Generate UUID and key for feedback (in real implementation, these would be unique)
        feedback_uuid = "example-uuid"  # In production, generate actual UUID
        feedback_key = "93de5448e0cb83c7f0cc081a1808ba37f1d2054ae0d73a643cf86e68d657baf9"  # In production, generate actual key
        
        return {
            'feedback_more_url': f"{base_url}/#/feedback/{post_id}/1/?uuid={feedback_uuid}&key={feedback_key}",
            'feedback_less_url': f"{base_url}/#/feedback/{post_id}/0/?uuid={feedback_uuid}&key={feedback_key}",
            'comment_url': f"{base_url}/{post_slug}/#ghost-comments-root"
        }

    def get_recent_posts_from_ghost(self, max_posts=5, days_back=30):
        """Fetch recent posts from Ghost Content API with enhanced filtering"""
        try:
            if not self.ghost_content_api_key:
                print("Ghost Content API key not found")
                return []
            
            # Auto-interval detection
            if self.auto_interval:
                days_back = self.detect_optimal_interval()
                print(f"🤖 Auto-detected interval: {days_back} days")
            
            # Calculate date filter for posts within the specified days
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_back)
            date_filter = cutoff_date.strftime('%Y-%m-%d')
            
            # Build the API URL
            base_url = self.ghost_admin_url.replace('/ghost/api/admin', '')
            url = f"{base_url}/ghost/api/content/posts/"
            
            headers = {
                'Accept-Version': 'v5.0'
            }
            
            params = {
                'key': self.ghost_content_api_key,
                'limit': max_posts,
                'order': 'published_at desc',
                'include': 'tags,authors',
                'formats': 'html,plaintext',
                'filter': f'published_at:>={date_filter}'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching posts from Ghost API: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            posts = data.get('posts', [])
            
            if not posts:
                print(f"No posts found in Ghost from the last {days_back} days")
                return []
            
            # Apply advanced filtering
            posts = self.filter_posts_by_criteria(posts)
            posts = self.enhance_post_images(posts)
            
            # Limit to max_posts after filtering
            posts = posts[:max_posts]
            
            print(f"Found {len(posts)} posts from Ghost from the last {days_back} days (after filtering)")
            for post in posts:
                tags = ', '.join([tag.get('name', '') for tag in post.get('tags', [])])
                featured = " [FEATURED]" if post.get('featured') else ""
                print(f"  - {post.get('title', 'Untitled')}{featured} (tags: {tags})")
            
            return posts
            
        except Exception as e:
            print(f"Error fetching posts from Ghost API: {e}")
            return []

    def get_latest_post_from_ghost(self):
        """Fetch the latest post from Ghost Content API (backwards compatibility)"""
        posts = self.get_recent_posts_from_ghost(max_posts=1)
        return posts[0] if posts else None

    def render_conditional_template(self, template, data):
        """Render template with conditional blocks and loops"""
        import re
        
        # Add default fallback values for missing data
        defaults = {
            'blog_title': 'Newsletter',
            'newsletter_interval': 'weekly',
            'newsletter_date': 'Recent',
            'featured_title': 'Latest Updates',
            'featured_content': '<p>Check out our latest content!</p>',
            'featured_url': '#',
            'posts': [],
            'blog_logo': '',
            'social_twitter_url': '',
            'newsletter_archive_url': ''
        }
        
        # Merge data with defaults (data takes precedence)
        template_data = {**defaults, **data}
        
        # Handle conditional blocks
        conditionals = [
            ('if_blog_logo', bool(template_data.get('blog_logo'))),
            ('if_featured_post', len(template_data.get('posts', [])) > 0),
            ('if_featured_image', len(template_data.get('posts', [])) > 0 and bool(template_data['posts'][0].get('picture'))),
            ('if_no_featured_image', len(template_data.get('posts', [])) > 0 and not bool(template_data['posts'][0].get('picture'))),
            ('if_featured_image_caption', bool(template_data.get('featured_image_caption'))),
            ('if_featured_excerpt', bool(template_data.get('featured_excerpt'))),
            ('if_additional_posts', len(template_data.get('posts', [])) > 1),
            ('if_social_sharing', bool(template_data.get('social_twitter_url'))),
            ('if_newsletter_archive', bool(template_data.get('newsletter_archive_url'))),
            # New newsletter-specific conditionals
            ('newsletter.header_image', bool(template_data.get('newsletter', {}).get('header_image'))),
            ('newsletter.settings.show_header_icon', template_data.get('newsletter', {}).get('settings', {}).get('show_header_icon', True)),
            ('newsletter.settings.show_header_title', template_data.get('newsletter', {}).get('settings', {}).get('show_header_title', True)),
            ('newsletter.settings.show_feature_image', template_data.get('newsletter', {}).get('settings', {}).get('show_feature_image', True)),
            ('newsletter.settings.show_excerpt', template_data.get('newsletter', {}).get('settings', {}).get('show_excerpt', True)),
            ('newsletter.settings.show_author', template_data.get('newsletter', {}).get('settings', {}).get('show_author', False)),
            ('newsletter.settings.show_latest_posts', template_data.get('newsletter', {}).get('settings', {}).get('show_latest_posts', True)),
            ('newsletter.settings.show_subscription_details', template_data.get('newsletter', {}).get('settings', {}).get('show_subscription_details', True)),
            ('newsletter.settings.footer_content', bool(template_data.get('newsletter', {}).get('settings', {}).get('footer_content'))),
            ('email.support_address', bool(template_data.get('email', {}).get('support_address'))),
        ]
        
        rendered = template
        
        # Process each conditional
        for condition_name, condition_value in conditionals:
            # Pattern to match conditional blocks
            pattern = r'{{#' + condition_name + r'}}(.*?){{/' + condition_name + r'}}'
            
            if condition_value:
                # Keep the content, remove the conditional tags
                rendered = re.sub(pattern, r'\1', rendered, flags=re.DOTALL)
            else:
                # Remove the entire conditional block
                rendered = re.sub(pattern, '', rendered, flags=re.DOTALL)
        
        # Replace template variables with fallback support
        for key, value in template_data.items():
            if key == 'posts':  # Skip the posts array used for conditionals
                continue
                
            # Handle triple braces for raw HTML content first
            if key in ['featured_content', 'additional_posts_content']:
                placeholder = '{{{' + key + '}}}'
                if placeholder in rendered:
                    rendered = rendered.replace(placeholder, str(value) if value is not None else '')
            
            # Handle double braces for escaped content
            placeholder = "{{" + key + "}}"
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, str(value) if value is not None else '')
        
        # Clean up any remaining unresolved double-brace variables only (not triple braces)
        # This pattern specifically matches {{word}} but not {{{word}}}
        rendered = re.sub(r'(?<!\{)\{\{[^{}]+\}\}(?!\})', '', rendered)
        
        return rendered

    def generate_additional_posts_html(self, posts):
        """Generate HTML for additional posts matching Ghost's exact structure"""
        if len(posts) <= 1:
            return ""
        
        additional_posts_html = ""
        additional_posts = posts[1:]  # Skip the featured post
        
        for i, post in enumerate(additional_posts):
            # Get post data safely
            post_title = post.get('title', 'Untitled')
            post_url = post.get('url', '#')
            post_excerpt = post.get('excerpt', '')
            
            # Get featured image - works with both processed and raw formats
            if 'picture' in post:
                featured_image = post.get('picture', '')
            else:
                featured_image = post.get('feature_image', '')
            
            # Generate the post HTML using Ghost's exact structure
            additional_posts_html += f'''
                                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;" width="100%">
                                                <tbody><tr>
                                                    <td class="latest-post" style="font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; font-size: 18px; vertical-align: top; color: #15212A; padding: 16px 0; max-width: 600px;" valign="top">
                                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;" width="100%">
                                                            <tbody><tr>
                                                                <td valign="top" align="left" class="latest-post-title" style="font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; font-size: 18px; vertical-align: top; color: #15212A; padding-right: 12px;">
                                                                    <h4 class="" style="margin-top: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; text-rendering: optimizeLegibility; line-height: 1.2em; margin: 0; padding: 2px 0 4px; font-size: 18px; font-weight: 700; color: #15212A;">
                                                                        <a href="{post_url}" style="overflow-wrap: anywhere; text-decoration: none; color: #15212A;" target="_blank">{post_title}</a>
                                                                    </h4>
                                                                        <p class="latest-post-excerpt" style="line-height: 1.6em; margin: 0; padding: 0; font-size: 15px; font-weight: 400; color: #15212a; color: rgba(0, 0, 0, 0.6);">
                                                                            <a href="{post_url}" style="overflow-wrap: anywhere; text-decoration: none; color: #15212a; color: rgba(0, 0, 0, 0.6);" target="_blank">{post_excerpt}</a>
                                                                        </p>
                                                                </td>'''
            
            # Add image column if featured image exists
            if featured_image:
                additional_posts_html += f'''
                                                                        <td width="100" class="latest-post-img" style="font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; font-size: 18px; vertical-align: top; color: #15212A;" valign="top">
                                                                            <a href="{post_url}" style="overflow-wrap: anywhere; display: block; height: 100px; overflow: hidden; color: inherit; text-decoration: none;" target="_blank">
                                                                                <img src="{featured_image}" width="100" height="100" style="border: none; -ms-interpolation-mode: bicubic; max-width: 100%; object-fit: cover;">
                                                                            </a>
                                                                        </td>'''
            
            # Close the row and table
            additional_posts_html += '''
                                                            </tr>
                                                        </tbody></table>
                                                    </td>
                                                </tr>
                                            </tbody></table>'''
        
        return additional_posts_html

    def load_template(self):
        """Load and return the HTML email template"""
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            template_path = os.path.join(script_dir, 'templates', 'ghost', 'newsletter_ghost_native.html')
            
            with open(template_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        except Exception as e:
            print(f"Error loading Ghost native template: {e}")
            return None

    def process_posts_for_template(self, posts):
        """Process Ghost posts into template-ready format"""
        try:
            processed_posts = []
            
            for i, post in enumerate(posts):
                # Extract basic post data
                post_url = post.get('url', '')
                if post_url and not post_url.startswith('http'):
                    post_url = f"{self.ghost_website_url}{post_url}"
                
                # Get tags and authors
                tags = post.get('tags', [])
                authors = post.get('authors', [])
                
                # Get first tag and author
                first_tag = tags[0].get('name') if tags else 'General'
                first_author = authors[0].get('name') if authors else self.from_name
                
                # Generate excerpt - use Ghost's excerpt or create from plaintext
                excerpt = post.get('excerpt', '')
                if not excerpt and post.get('plaintext'):
                    excerpt = post.get('plaintext', '')[:200] + '...' if len(post.get('plaintext', '')) > 200 else post.get('plaintext', '')
                
                # Process content for featured post (first post gets full HTML, others get excerpt)
                if i == 0:  # Featured post
                    content = self.process_content(post.get('html', ''))
                else:  # Regular posts get excerpt only
                    content = excerpt
                
                processed_post = {
                    'title': post.get('title', 'Untitled'),
                    'text': content,
                    'url': post_url,
                    'tag': first_tag,
                    'author': first_author,
                    'picture': post.get('feature_image', ''),
                    'excerpt': excerpt,
                    'published_at': post.get('published_at', ''),
                    'raw_html': post.get('html', ''),
                    'plaintext': post.get('plaintext', '')
                }
                
                processed_posts.append(processed_post)
            
            return processed_posts
            
        except Exception as e:
            print(f"Error processing posts for template: {e}")
            return []

    def generate_newsletter_data(self, posts, blog_settings, newsletter_interval='weekly', branding_settings=None):
        """Generate complete newsletter data structure for template"""
        try:
            # Process posts
            processed_posts = self.process_posts_for_template(posts)
            
            # Get newsletter-specific settings
            newsletter_config = self.get_newsletter_settings()
            
            # Get branding settings with defaults
            if branding_settings is None:
                branding_settings = {}
            
            # Extract branding colors with fallbacks
            accent_color = branding_settings.get('accent_color', '#2b546d')  # Your current accent color as fallback
            brand_color = branding_settings.get('brand_color', accent_color)  # Use accent color if no brand color set
            
            # Extract other branding elements
            site_logo = branding_settings.get('logo', blog_settings.get('logo', ''))
            site_icon = branding_settings.get('icon', blog_settings.get('icon', ''))
            cover_image = branding_settings.get('cover_image', blog_settings.get('cover_image', ''))
            
            print(f"🎨 Using branding colors - Accent: {accent_color}, Brand: {brand_color}")
            if accent_color != '#2b546d':
                print(f"  ℹ️  Custom accent color detected: {accent_color}")
            if brand_color and brand_color != accent_color:
                print(f"  ℹ️  Secondary brand color: {brand_color}")
            
            # Get newsletter-specific configuration
            newsletter_settings = {}
            email_settings = {}
            header_image = None
            sender_name = self.from_name
            
            if newsletter_config:
                active_newsletter = newsletter_config.get('newsletter', {})
                email_settings = newsletter_config.get('email_settings', {})
                
                # Extract newsletter-specific settings
                newsletter_settings = {
                    'header_image': active_newsletter.get('header_image'),
                    'show_header_icon': active_newsletter.get('show_header_icon', True),
                    'show_header_title': active_newsletter.get('show_header_title', True),
                    'show_feature_image': active_newsletter.get('show_feature_image', True),
                    'show_excerpt': active_newsletter.get('show_excerpt', True),
                    'show_author': active_newsletter.get('show_author'),
                    'footer_content': active_newsletter.get('footer_content'),
                    'sender_name': active_newsletter.get('sender_name'),
                    'sender_email': active_newsletter.get('sender_email'),
                    'subject_prefix': active_newsletter.get('subject_prefix'),
                    'title_font_category': active_newsletter.get('title_font_category', 'sans_serif'),
                    'body_font_category': active_newsletter.get('body_font_category', 'sans_serif'),
                    'title_alignment': active_newsletter.get('title_alignment', 'center'),
                    'background_color': active_newsletter.get('background_color', 'light')
                }
                
                header_image = newsletter_settings.get('header_image')
                if newsletter_settings.get('sender_name'):
                    sender_name = newsletter_settings.get('sender_name')
                
                print(f"📰 Newsletter settings applied:")
                print(f"  • Header image: {header_image or 'None'}")
                print(f"  • Sender name: {sender_name}")
                print(f"  • Font: {newsletter_settings.get('title_font_category')}")
                print(f"  • Background: {newsletter_settings.get('background_color')}")
            
            # Generate newsletter date
            now = datetime.now()
            if newsletter_interval.lower() == 'weekly':
                # For weekly, show week start date
                days_since_monday = now.weekday()
                week_start = now - timedelta(days=days_since_monday)
                formatted_date = week_start.strftime("%B %d, %Y")
            elif newsletter_interval.lower() == 'monthly':
                formatted_date = now.strftime("%B %Y")
            else:  # daily
                formatted_date = now.strftime("%B %d, %Y")
            
            # Build newsletter data structure matching original.html expectations
            newsletter_data = {
                'blog': {
                    'title': blog_settings.get('title', self.from_name),
                    'logo': site_logo,
                    'icon': site_icon,
                    'cover_image': cover_image,
                    'description': blog_settings.get('description', ''),
                    'unsubscribe': '{{unsubscribe_url}}',  # Will be replaced per email
                    'post': processed_posts,
                    'original_posts': posts,  # Keep original Ghost posts for ID/slug access
                    'website_url': self.ghost_website_url
                },
                'newsletter': {
                    'interval': newsletter_interval,
                    'date': formatted_date,
                    'archive_url': f"{self.ghost_website_url}/newsletters" if self.ghost_website_url else "",
                    'social_sharing': self.generate_social_sharing_data(processed_posts),
                    'sender_name': sender_name,
                    'header_image': header_image,
                    'settings': newsletter_settings
                },
                'email': {
                    'track_opens': email_settings.get('email_track_opens', True),
                    'track_clicks': email_settings.get('email_track_clicks', True),
                    'default_address': email_settings.get('default_email_address'),
                    'support_address': email_settings.get('support_email_address')
                },
                'branding': {
                    'accent_color': accent_color,
                    'brand_color': brand_color,
                    'primary_color': accent_color,  # Alias for template compatibility
                    'secondary_color': brand_color,  # Alias for template compatibility
                    'text_color': '#15212A',  # Default Ghost text color
                    'light_text_color': '#738a94',  # Default Ghost light text color
                    'background_color': '#ffffff',  # Default background
                    'border_color': '#e0e7eb'  # Default Ghost border color
                }
            }
            
            return newsletter_data
            
        except Exception as e:
            print(f"Error generating newsletter data: {e}")
            return None

    def process_content(self, content):
        """Process HTML content for email compatibility"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Style paragraphs
            p_style = "font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; font-size: 18px; font-weight: normal; margin: 0 0 16px 0; line-height: 1.6; color: #495057;"
            
            for p_tag in soup.find_all('p'):
                p_tag['style'] = p_style
            
            # Style images
            for img_tag in soup.find_all('img'):
                img_tag['style'] = "width: 100%; height: auto; border-radius: 4px; margin: 16px 0;"
                img_tag.attrs.pop('width', None)
                img_tag.attrs.pop('height', None)
            
            # Style headings
            heading_sizes = [32, 26, 21, 19, 17, 15]  # Match Ghost's responsive font sizes
            for i, h_tag in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                font_size = heading_sizes[i]
                h_style = f"font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; font-size: {font_size}px; font-weight: 700; margin: 24px 0 16px 0; line-height: 1.3; color: #2c3e50;"
                
                for heading in soup.find_all(h_tag):
                    heading['style'] = h_style
            
            # Style links
            for a_tag in soup.find_all('a'):
                a_tag['style'] = "color: #007bff; text-decoration: none; font-weight: 500;"
            
            # Style figure captions
            for figcaption in soup.find_all('figcaption'):
                figcaption['style'] = "font-family: Inter, -apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica neue, helvetica, ubuntu, roboto, noto, segoe ui, arial, sans-serif; font-size: 14px; color: #738a94; text-align: center; margin: 8px 0 16px 0; line-height: 1.4; font-style: italic;"
                
                # Style any span elements within figcaption (Ghost often wraps caption text in spans)
                for span in figcaption.find_all('span'):
                    # Preserve any existing styling but ensure text wrapping
                    existing_style = span.get('style', '')
                    if 'white-space: pre-wrap' in existing_style:
                        # Clean up the existing style and add display block
                        cleaned_style = existing_style.replace('white-space: pre-wrap', 'white-space: pre-wrap; display: block; word-wrap: break-word')
                        span['style'] = cleaned_style
                    else:
                        span['style'] = "display: block; word-wrap: break-word;"
            
            # Style bookmark cards
            for bookmark_card in soup.find_all('figure', class_='kg-bookmark-card'):
                # Create new email-compatible structure
                bookmark_link = bookmark_card.find('a', class_='kg-bookmark-container')
                if bookmark_link:
                    href = bookmark_link.get('href', '#')
                    
                    # Extract content elements
                    title_elem = bookmark_card.find('div', class_='kg-bookmark-title')
                    desc_elem = bookmark_card.find('div', class_='kg-bookmark-description')
                    icon_elem = bookmark_card.find('img', class_='kg-bookmark-icon')
                    thumbnail_elem = bookmark_card.find('div', class_='kg-bookmark-thumbnail')
                    author_elem = bookmark_card.find('span', class_='kg-bookmark-author')
                    
                    title = title_elem.get_text() if title_elem else 'Bookmark'
                    description = desc_elem.get_text() if desc_elem else ''
                    icon_src = icon_elem.get('src', '') if icon_elem else ''
                    author = author_elem.get_text() if author_elem else ''
                    
                    # Get thumbnail image
                    thumbnail_src = ''
                    if thumbnail_elem:
                        thumbnail_img = thumbnail_elem.find('img')
                        if thumbnail_img:
                            thumbnail_src = thumbnail_img.get('src', '')
                    
                    # Create email-compatible bookmark card
                    email_bookmark = soup.new_tag('table')
                    email_bookmark['style'] = "width: 100%; max-width: 600px; margin: 24px 0; border: 1px solid #e0e7eb; border-radius: 8px; overflow: hidden; background-color: #ffffff;"
                    email_bookmark['cellpadding'] = "0"
                    email_bookmark['cellspacing'] = "0"
                    email_bookmark['border'] = "0"
                    
                    # Create main row
                    main_row = soup.new_tag('tr')
                    
                    # Content cell
                    content_cell = soup.new_tag('td')
                    content_cell['style'] = "padding: 20px; vertical-align: top;"
                    
                    # Title
                    title_div = soup.new_tag('div')
                    title_div['style'] = "font-family: Inter, -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 600; color: #15212A; margin-bottom: 8px; line-height: 1.4;"
                    title_div.string = title
                    content_cell.append(title_div)
                    
                    # Description
                    if description:
                        desc_div = soup.new_tag('div')
                        desc_div['style'] = "font-family: Inter, -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #738a94; margin-bottom: 12px; line-height: 1.5; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;"
                        desc_div.string = description[:150] + '...' if len(description) > 150 else description
                        content_cell.append(desc_div)
                    
                    # Metadata with icon and author
                    if icon_src or author:
                        meta_div = soup.new_tag('div')
                        meta_div['style'] = "display: flex; align-items: center; font-family: Inter, -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif; font-size: 13px; color: #738a94;"
                        
                        if icon_src:
                            icon_img = soup.new_tag('img')
                            icon_img['src'] = icon_src
                            icon_img['alt'] = ''
                            icon_img['style'] = "width: 16px; height: 16px; margin-right: 8px; border-radius: 2px;"
                            meta_div.append(icon_img)
                        
                        if author:
                            author_span = soup.new_tag('span')
                            author_span.string = author
                            meta_div.append(author_span)
                        
                        content_cell.append(meta_div)
                    
                    main_row.append(content_cell)
                    
                    # Thumbnail cell (if available)
                    if thumbnail_src:
                        thumbnail_cell = soup.new_tag('td')
                        thumbnail_cell['style'] = "width: 120px; padding: 20px 20px 20px 0; vertical-align: top;"
                        
                        thumbnail_img = soup.new_tag('img')
                        thumbnail_img['src'] = thumbnail_src
                        thumbnail_img['alt'] = ''
                        thumbnail_img['style'] = "width: 120px; height: 80px; object-fit: cover; border-radius: 4px;"
                        
                        thumbnail_cell.append(thumbnail_img)
                        main_row.append(thumbnail_cell)
                    
                    email_bookmark.append(main_row)
                    
                    # Wrap in link
                    link_wrapper = soup.new_tag('a')
                    link_wrapper['href'] = href
                    link_wrapper['style'] = "text-decoration: none; color: inherit; display: block;"
                    link_wrapper['target'] = '_blank'
                    link_wrapper.append(email_bookmark)
                    
                    # Replace the original bookmark card
                    bookmark_card.replace_with(link_wrapper)
            
            # Style callout cards
            for callout_card in soup.find_all('div', class_='kg-callout-card'):
                # Determine callout type and set appropriate background color
                callout_type = 'grey'  # default
                if 'kg-callout-card-blue' in callout_card.get('class', []):
                    callout_type = 'blue'
                elif 'kg-callout-card-green' in callout_card.get('class', []):
                    callout_type = 'green'
                elif 'kg-callout-card-yellow' in callout_card.get('class', []):
                    callout_type = 'yellow'
                elif 'kg-callout-card-red' in callout_card.get('class', []):
                    callout_type = 'red'
                elif 'kg-callout-card-pink' in callout_card.get('class', []):
                    callout_type = 'pink'
                elif 'kg-callout-card-purple' in callout_card.get('class', []):
                    callout_type = 'purple'
                
                # Define color schemes for different callout types
                color_schemes = {
                    'grey': {'bg': '#f8f9fa', 'border': '#e9ecef', 'text': '#495057'},
                    'blue': {'bg': '#e7f3ff', 'border': '#b3d9ff', 'text': '#0c5aa6'},
                    'green': {'bg': '#e8f5e8', 'border': '#c3e6c3', 'text': '#0f5132'},
                    'yellow': {'bg': '#fff3cd', 'border': '#ffd60a', 'text': '#664d03'},
                    'red': {'bg': '#f8d7da', 'border': '#f5c2c7', 'text': '#721c24'},
                    'pink': {'bg': '#f3e2f3', 'border': '#e1bee7', 'text': '#7b1fa2'},
                    'purple': {'bg': '#e1e7ff', 'border': '#c5d1ff', 'text': '#4c1d95'}
                }
                
                colors = color_schemes.get(callout_type, color_schemes['grey'])
                
                # Apply email-compatible styling to the callout card
                callout_card['style'] = f"background-color: {colors['bg']}; border: 1px solid {colors['border']}; border-radius: 6px; padding: 16px 20px; margin: 24px 0; font-family: Inter, -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;"
                
                # Style the callout text content
                callout_text = callout_card.find('div', class_='kg-callout-text')
                if callout_text:
                    callout_text['style'] = f"color: {colors['text']}; font-size: 16px; line-height: 1.5; margin: 0;"
                    
                    # Style any nested elements within the callout text
                    for elem in callout_text.find_all(['i', 'em', 'strong', 'b']):
                        existing_style = elem.get('style', '')
                        # Preserve existing style but ensure proper text wrapping
                        if 'white-space: pre-wrap' in existing_style:
                            # Clean up the existing style and add color and display properties
                            cleaned_style = existing_style.replace('white-space: pre-wrap', f'white-space: pre-wrap; color: {colors["text"]}; display: block; word-wrap: break-word')
                            elem['style'] = cleaned_style
                        else:
                            elem['style'] = f"color: {colors['text']}; word-wrap: break-word;"
            
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
            now = datetime.now()
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

    def render_newsletter_template(self, template, newsletter_data):
        """Render the email template with newsletter data using the new template system"""
        try:
            # Process content with UTM tags for all posts
            for post in newsletter_data['blog']['post']:
                if post['url']:
                    post['text'] = self.add_utm_tags(post['text'], post['url'])
            
            # Prepare template data
            posts = newsletter_data['blog']['post']
            featured_post = posts[0] if posts else {}
            
            # Get original post for feedback URLs (with ID and slug)
            original_posts = newsletter_data['blog'].get('original_posts', [])
            featured_original_post = original_posts[0] if original_posts else {}
            
            # Generate additional posts HTML
            additional_posts_html = self.generate_additional_posts_html(posts)
            
            # Template data for the new system
            template_data = {
                # Legacy compatibility variables
                'blog_title': newsletter_data['blog']['title'],
                'blog_logo': newsletter_data['blog']['logo'],
                'newsletter_interval': newsletter_data['newsletter']['interval'],
                'newsletter_date': newsletter_data['newsletter']['date'],
                'newsletter_preview': featured_post.get('excerpt', '')[:100] + '...' if featured_post.get('excerpt') else '',
                'featured_title': featured_post.get('title', ''),
                'featured_excerpt': featured_post.get('excerpt', ''),
                'featured_content': featured_post.get('text', ''),
                'featured_url': featured_post.get('url', ''),
                'featured_tag': featured_post.get('tag', ''),
                'featured_author': featured_post.get('author', ''),
                'featured_image': featured_post.get('picture', ''),
                'featured_image_caption': featured_post.get('feature_image_caption', ''),
                'additional_posts_content': additional_posts_html,
                'unsubscribe_url': '{{unsubscribe_url}}',  # Will be replaced per email
                'posts': posts,  # For conditionals
                
                # Flat template variables for compatibility
                'blog.title': newsletter_data['blog']['title'],
                'blog.logo': newsletter_data['blog']['logo'],
                'blog.icon': newsletter_data['blog']['icon'],
                'blog.website_url': newsletter_data['blog']['website_url'],
                'blog.description': newsletter_data['blog']['description'],
                'newsletter.header_image': newsletter_data['newsletter']['header_image'],
                'newsletter.sender_name': newsletter_data['newsletter']['sender_name'],
                'newsletter.settings.show_header_icon': newsletter_data['newsletter']['settings'].get('show_header_icon', True),
                'newsletter.settings.show_header_title': newsletter_data['newsletter']['settings'].get('show_header_title', True),
                'newsletter.settings.show_feature_image': newsletter_data['newsletter']['settings'].get('show_feature_image', True),
                'newsletter.settings.show_excerpt': newsletter_data['newsletter']['settings'].get('show_excerpt', True),
                'newsletter.settings.show_author': newsletter_data['newsletter']['settings'].get('show_author', False),
                'newsletter.settings.show_latest_posts': newsletter_data['newsletter']['settings'].get('show_latest_posts', True),
                'newsletter.settings.show_subscription_details': newsletter_data['newsletter']['settings'].get('show_subscription_details', True),
                'newsletter.settings.footer_content': newsletter_data['newsletter']['settings'].get('footer_content', ''),
                'email.support_address': newsletter_data['email']['support_address'],
                
                # New structured data for template
                'blog': {
                    'title': newsletter_data['blog']['title'],
                    'logo': newsletter_data['blog']['logo'],
                    'icon': newsletter_data['blog']['icon'],
                    'website_url': newsletter_data['blog']['website_url'],
                    'description': newsletter_data['blog']['description']
                },
                'newsletter': {
                    'interval': newsletter_data['newsletter']['interval'],
                    'date': newsletter_data['newsletter']['date'],
                    'sender_name': newsletter_data['newsletter']['sender_name'],
                    'header_image': newsletter_data['newsletter']['header_image'],
                    'settings': newsletter_data['newsletter']['settings']
                },
                'email': {
                    'track_opens': newsletter_data['email']['track_opens'],
                    'track_clicks': newsletter_data['email']['track_clicks'],
                    'support_address': newsletter_data['email']['support_address']
                },
                
                # Member/Subscription details (with fallback for debug)
                'member_name': 'Jamie Larson',  # Sample data for debug
                'member_email': 'jamie@example.com',  # Sample data for debug
                'member_created_at': '17 July 2023',  # Sample data for debug
                'subscription_renewal_date': '17 Jul 2024',  # Sample data for debug
                'manage_subscription_url': '#manage-subscription',  # Sample URL for debug
                
                # Phase 3 Enhanced Features
                'social_twitter_url': newsletter_data['newsletter']['social_sharing'].get('twitter_url', ''),
                'social_facebook_url': newsletter_data['newsletter']['social_sharing'].get('facebook_url', ''),
                'social_linkedin_url': newsletter_data['newsletter']['social_sharing'].get('linkedin_url', ''),
                'newsletter_archive_url': newsletter_data['newsletter'].get('archive_url', ''),
                
                # Branding and colors from Ghost API
                'accent_color': newsletter_data['branding']['accent_color'],
                'brand_color': newsletter_data['branding']['brand_color'],
                'primary_color': newsletter_data['branding']['primary_color'],
                'secondary_color': newsletter_data['branding']['secondary_color'],
                'text_color': newsletter_data['branding']['text_color'],
                'light_text_color': newsletter_data['branding']['light_text_color'],
                'background_color': newsletter_data['branding']['background_color'],
                'border_color': newsletter_data['branding']['border_color'],
                
                # Add feedback URLs using original post data
                **self.generate_feedback_urls(featured_original_post),
            }
            
            # Apply conditional rendering
            rendered = self.render_conditional_template(template, template_data)
            
            # Debug: Print template data structure
            print(f"🐛 Template data keys: {list(template_data.keys())}")
            if 'newsletter' in template_data:
                print(f"🐛 Newsletter data: {template_data['newsletter']}")
            if 'blog' in template_data:
                print(f"🐛 Blog data: {template_data['blog']}")
            if 'email' in template_data:
                print(f"🐛 Email data: {template_data['email']}")
            
            # Helper function to handle nested object references
            def replace_nested_template_vars(text, data, prefix=''):
                """Replace template variables including nested objects"""
                import re
                
                # Handle simple conditionals first ({{#if variable}})
                if_pattern = r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}'
                
                def process_conditional(match):
                    condition = match.group(1).strip()
                    content = match.group(2)
                    
                    # Evaluate condition from nested data
                    value = get_nested_value(data, condition)
                    return content if value else ''
                
                # Replace conditionals
                text = re.sub(if_pattern, process_conditional, text, flags=re.DOTALL)
                
                # Handle nested object references like {{blog.title}}, {{newsletter.settings.show_header_icon}}
                for key, value in data.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        # Recursively handle nested objects
                        text = replace_nested_template_vars(text, value, current_path)
                    else:
                        # Replace the template variable
                        placeholder = '{{' + current_path + '}}'
                        text = text.replace(placeholder, str(value) if value is not None else '')
                
                return text
            
            def get_nested_value(data, path):
                """Get value from nested object using dot notation"""
                try:
                    keys = path.split('.')
                    value = data
                    for key in keys:
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            return False
                    return bool(value) if value is not None else False
                except:
                    return False
            
            # Replace nested template variables
            rendered = replace_nested_template_vars(rendered, template_data)
            
            # Debug: Check if key variables were replaced
            if 'https://brunoamaral.eu/content/images/2025/08/IMG_8250-4.jpeg' in rendered:
                print("✅ Header image was successfully replaced")
            else:
                print("❌ Header image replacement failed")
                # Check if the placeholder is still there
                if '{{newsletter.header_image}}' in rendered:
                    print("🐛 Template still contains: {{newsletter.header_image}}")
            
            if 'bruno-1.png' in rendered:
                print("✅ Blog icon was successfully replaced")
            else:
                print("❌ Blog icon replacement failed")
                if '{{blog.icon}}' in rendered:
                    print("🐛 Template still contains: {{blog.icon}}")
            
            # Replace template variables (legacy compatibility)
            for key, value in template_data.items():
                if key == 'posts':  # Skip the posts array used for conditionals
                    continue
                if isinstance(value, dict):  # Skip nested objects (already handled above)
                    continue
                    
                if key in ['featured_content', 'additional_posts_content']:
                    # Handle triple braces for raw HTML content
                    placeholder = '{{{' + key + '}}}'
                    rendered = rendered.replace(placeholder, str(value) if value else '')
                else:
                    # Handle double braces for escaped content
                    placeholder = '{{' + key + '}}'
                    rendered = rendered.replace(placeholder, str(value) if value else '')
            
            return rendered
            
        except Exception as e:
            print(f"Error rendering newsletter template: {e}")
            import traceback
            traceback.print_exc()
            return None

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
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%B %d, %Y")
                except:
                    formatted_date = datetime.now().strftime("%B %d, %Y")
            else:
                formatted_date = datetime.now().strftime("%B %d, %Y")
            
            # Process content
            processed_content = self.process_content(post_content)
            processed_content = self.add_utm_tags(processed_content, post_url)
            
            # Template variables
            template_vars = {
                'newsletter_title': f"{self.from_name}",
                'post_excerpt': post_excerpt[:150] + '...' if len(post_excerpt) > 150 else post_excerpt,
                'author_name': self.from_name,
                'newsletter_name': '',
                'publish_date': formatted_date,
                'post_url': post_url,
                'featured_image': featured_image,
                'post_title': post_title,
                'post_content': processed_content,
                'website_url': self.ghost_website_url,
                'footer_address': os.getenv('GHOST_NEWSLETTER_ADDRESS', f'{self.from_name}'),
                'unsubscribe_url': '{{unsubscribe_url}}',  # Will be replaced per email
                
                # Add feedback URLs
                **self.generate_feedback_urls(post)
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
            
            # Get recent posts
            print(f"📰 Fetching up to {self.max_posts} posts from the last {self.days_back} days...")
            recent_posts = self.get_recent_posts_from_ghost(self.max_posts, self.days_back)
            if not recent_posts:
                print("No posts found. Exiting.")
                return False
            
            # Get blog settings and branding
            print("⚙️ Fetching blog settings and branding...")
            blog_settings = self.get_blog_settings_from_ghost()
            
            # Get comprehensive branding settings for styling
            print("🎨 Fetching branding settings for dynamic styling...")
            branding_data = self.get_comprehensive_branding_settings()
            branding_settings = branding_data.get('branding_settings', {}) if branding_data else {}
            
            # Generate newsletter data
            print("📊 Generating newsletter data structure...")
            newsletter_data = self.generate_newsletter_data(recent_posts, blog_settings, self.newsletter_interval, branding_settings)
            if not newsletter_data:
                print("Failed to generate newsletter data. Exiting.")
                return False
            
            # Get featured post title for email subject
            featured_post_title = newsletter_data['blog']['post'][0]['title'] if newsletter_data['blog']['post'] else "Newsletter"
            
            print(f"Newsletter will include {len(newsletter_data['blog']['post'])} posts:")
            for i, post in enumerate(newsletter_data['blog']['post']):
                post_type = "Featured" if i == 0 else "Regular"
                print(f"  {i+1}. [{post_type}] {post['title']}")
            
            # Load template
            print("📧 Loading email template...")
            template = self.load_template()
            if not template:
                print("Failed to load template. Exiting.")
                return False
            
            # Render template with newsletter data
            print("🎨 Rendering email content...")
            email_content = self.render_newsletter_template(template, newsletter_data)
            if not email_content:
                print("Failed to render template. Exiting.")
                return False
            
            # Save rendered content for debugging if in dry run mode
            if dry_run:
                try:
                    script_dir = os.path.dirname(os.path.realpath(__file__))
                    debug_path = os.path.join(script_dir, 'debug_newsletter.html')
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(email_content.replace('{{unsubscribe_url}}', '#unsubscribe'))
                    print(f"🐛 Debug: Rendered newsletter saved to {debug_path}")
                except Exception as e:
                    print(f"Warning: Could not save debug file: {e}")
            
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
                    newsletter_name = f"{newsletter_data['blog']['title']}"
                    email_subject = f"{newsletter_name}: {featured_post_title}"
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
            print(f"   📝 Subject: {email_subject}")
            
            return sent_count > 0
            
        except Exception as e:
            print(f"Error in send_newsletter: {e}")
            return False


def main():
    """Main function"""
    try:
        # Setup argument parser
        parser = argparse.ArgumentParser(description='Send newsletter using Ghost API with enhanced Phase 3 features.')
        parser.add_argument('--send', action='store_true', help='Send to all subscribers (default is dry run)')
        parser.add_argument('--max-posts', type=int, default=5, help='Maximum number of posts to include (default: 5)')
        parser.add_argument('--days-back', type=int, default=30, help='Include posts from last N days (default: 30)')
        parser.add_argument('--interval', choices=['daily', 'weekly', 'monthly'], default='weekly', help='Newsletter interval (default: weekly)')
        
        # Phase 3 Enhanced Features
        parser.add_argument('--auto-interval', action='store_true', help='Auto-detect optimal newsletter interval based on posting frequency')
        parser.add_argument('--featured-only', action='store_true', help='Include only featured posts')
        parser.add_argument('--filter-tags', nargs='+', help='Filter posts by tags (space-separated list)')
        
        # Testing and debugging options
        parser.add_argument('--check-branding', action='store_true', help='Check available branding and design settings from Ghost API')
        parser.add_argument('--check-newsletter', action='store_true', help='Check newsletter configuration and design settings from Ghost API')
        parser.add_argument('--check-theme', action='store_true', help='Check theme information from Ghost API')
        parser.add_argument('--analyze-branding', action='store_true', help='Comprehensive analysis of branding capabilities and recommendations')
        
        args = parser.parse_args()
        
        # Create newsletter sender with configuration
        sender = GhostNewsletterSender(
            max_posts=args.max_posts,
            days_back=args.days_back,
            newsletter_interval=args.interval,
            filter_tags=args.filter_tags,
            featured_only=args.featured_only,
            auto_interval=args.auto_interval
        )
        
        # Check branding settings if requested
        if args.check_branding:
            print("🎨 Checking Ghost API branding and design settings...")
            branding_data = sender.get_comprehensive_branding_settings()
            if branding_data:
                print("\n✅ Branding check completed successfully!")
            else:
                print("\n❌ Failed to fetch branding settings")
            sys.exit(0)
            
        # Check newsletter settings if requested
        if args.check_newsletter:
            print("📰 Checking Ghost newsletter configuration...")
            newsletter_data = sender.get_newsletter_settings()
            if newsletter_data:
                print("\n📰 NEWSLETTER CONFIGURATION:")
                print("=" * 50)
                
                newsletter = newsletter_data.get('newsletter', {})
                email_settings = newsletter_data.get('email_settings', {})
                
                print(f"\n📧 Active Newsletter:")
                print(f"  • Name: {newsletter.get('name')}")
                print(f"  • Sender: {newsletter.get('sender_name')} <{newsletter.get('sender_email')}>")
                print(f"  • Reply-to: {newsletter.get('sender_reply_to')}")
                
                print(f"\n🎨 Design Settings:")
                print(f"  • Header image: {newsletter.get('header_image') or 'None'}")
                print(f"  • Title font: {newsletter.get('title_font_category')}")
                print(f"  • Body font: {newsletter.get('body_font_category')}")
                print(f"  • Title alignment: {newsletter.get('title_alignment')}")
                print(f"  • Background: {newsletter.get('background_color')}")
                
                print(f"\n📝 Content Settings:")
                print(f"  • Show header icon: {newsletter.get('show_header_icon')}")
                print(f"  • Show header title: {newsletter.get('show_header_title')}")
                print(f"  • Show feature image: {newsletter.get('show_feature_image')}")
                print(f"  • Show excerpt: {newsletter.get('show_excerpt')}")
                print(f"  • Show author: {newsletter.get('show_author')}")
                print(f"  • Footer content: {newsletter.get('footer_content') or 'None'}")
                
                print(f"\n⚙️ Email Settings:")
                for key, value in email_settings.items():
                    print(f"  • {key}: {value}")
                
                print("\n✅ Newsletter configuration check completed!")
            else:
                print("\n❌ Failed to fetch newsletter settings")
            sys.exit(0)
            
        # Check theme information if requested
        if args.check_theme:
            print("🎭 Checking Ghost API theme information...")
            theme_data = sender.get_theme_information()
            if theme_data:
                print("\n✅ Theme check completed successfully!")
            else:
                print("\n❌ Failed to fetch theme information")
            sys.exit(0)
            
        # Analyze branding capabilities if requested
        if args.analyze_branding:
            sender.analyze_branding_capabilities()
            sys.exit(0)
        
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
