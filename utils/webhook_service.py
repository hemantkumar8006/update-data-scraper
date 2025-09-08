import requests
import json
import logging
from typing import Dict, Any
from datetime import datetime

class WebhookService:
    """Service for sending notifications to external webhook APIs"""
    
    def __init__(self, webhook_url: str, webhook_secret: str):
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification to webhook API
        
        Args:
            notification_data: Dictionary containing notification details
            
        Returns:
            Dictionary with webhook response and status
        """
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Secret": self.webhook_secret
                }
            
            # Prepare payload
            payload = self._format_payload(notification_data)
            
            # Print detailed debugging information
            print(f"\n🔍 WEBHOOK DEBUG INFO:")
            print(f"📡 Webhook URL: {self.webhook_url}")
            print(f"🔑 Webhook Secret: {self.webhook_secret}")
            print(f"📋 Headers: {headers}")
            print(f"📦 Full Payload:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print(f"📏 Payload Size: {len(json.dumps(payload))} characters")
            print(f"🔍 WEBHOOK DEBUG END\n")
            
            # Log payload for debugging (first 200 chars)
            payload_preview = json.dumps(payload)[:200] + "..." if len(json.dumps(payload)) > 200 else json.dumps(payload)
            self.logger.info(f"Sending webhook payload: {payload_preview}")
            
            # Send POST request
            print(f"🚀 Sending POST request to: {self.webhook_url}")
            response = requests.post(
                self.webhook_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Print response debugging information
            print(f"📨 Response Status Code: {response.status_code}")
            print(f"📨 Response Headers: {dict(response.headers)}")
            print(f"📨 Response Text: {response.text}")
            
            # Check response
            if response.status_code == 200:
                try:
                    webhook_response = response.json()
                    print(f"✅ Webhook Success Response: {webhook_response}")
                    self.logger.info(f"Webhook notification sent successfully: {webhook_response}")
                    return {
                        "success": True,
                        "webhook_response": webhook_response,
                        "status_code": response.status_code
                    }
                except json.JSONDecodeError:
                    print(f"⚠️  Webhook returned 200 but invalid JSON: {response.text}")
                    return {
                        "success": True,
                        "webhook_response": {"message": "Success but no JSON response"},
                        "status_code": response.status_code
                    }
            else:
                print(f"❌ Webhook Failed - Status: {response.status_code}, Text: {response.text}")
                self.logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Webhook Request Exception: {e}")
            print(f"❌ Exception Type: {type(e).__name__}")
            self.logger.error(f"Webhook request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
        except Exception as e:
            print(f"❌ Unexpected Webhook Error: {e}")
            print(f"❌ Exception Type: {type(e).__name__}")
            self.logger.error(f"Unexpected error sending webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    def _format_payload(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format notification data into webhook payload
        
        Args:
            notification_data: Raw notification data
            
        Returns:
            Formatted payload for webhook API
        """
        # Extract basic information
        title = notification_data.get('title', 'Exam Update')
        content = notification_data.get('content_summary', notification_data.get('content', ''))
        source = notification_data.get('source', 'exam_scraper')
        priority = notification_data.get('priority', 'medium')
        url = notification_data.get('url', '')
        date = notification_data.get('date', '')
        scraped_at = notification_data.get('scraped_at', '')
        
        # Determine exam type from source or title
        exam_type = self._determine_exam_type(notification_data)
        
        # Format exam name based on exam type
        exam_name_mapping = {
            'jee': 'JEE Main',
            'jee_adv': 'JEE Advanced', 
            'gate': 'GATE',
            'upsc': 'UPSC Civil Services',
            'cat': 'CAT',
            'neet': 'NEET',
            'demo': 'Demo Notification'
        }
        exam_name = exam_name_mapping.get(exam_type.lower(), exam_type.upper())
        
        # Extract time from date or use current time
        exam_time = self._extract_time_from_date(date, scraped_at)
        
        # Determine location based on exam type and source
        location = self._determine_location(exam_type, source, title, notification_data)
        
        # Create payload matching the bot's expected format
        # Only include the exact fields the bot expects
        payload = {
            "title": title,
            "content": content,
            "notificationType": "exam_updates",
            "metadata": {
                "examName": exam_name,
                "examDate": date,
                "examTime": exam_time,
                "location": location,
                "priority": priority,
                "source": source,
                "url": url
            }
        }
        
        return payload
    
    def _determine_exam_type(self, notification_data: Dict[str, Any]) -> str:
        """
        Determine exam type from notification data
        
        Args:
            notification_data: Raw notification data
            
        Returns:
            Exam type string
        """
        # Check if exam_type is explicitly provided
        exam_type = notification_data.get('exam_type', '').lower()
        if exam_type:
            return exam_type
        
        # Determine from source
        source = notification_data.get('source', '').lower()
        title = notification_data.get('title', '').lower()
        
        # Check for JEE Advanced first (more specific)
        if ('jee advanced' in source or 'jeeadv' in source or 
            'jee advanced' in title or 'jeeadv' in title):
            return 'jee_adv'
        
        # Check for GATE
        elif ('gate' in source or 'gate' in title):
            return 'gate'
        
        # Check for UPSC
        elif ('upsc' in source or 'upsc' in title):
            return 'upsc'
        
        # Check for NEET
        elif ('neet' in source or 'neet' in title):
            return 'neet'
        
        # Check for CAT
        elif ('cat' in source or 'cat' in title):
            return 'cat'
        
        # Check for JEE Main (or any JEE that's not Advanced)
        elif ('jee' in source or 'jee' in title or 'nta' in source):
            return 'jee'
        
        # Check for demo notifications
        elif ('demo' in source or 'demo' in title or 'bot testing' in source):
            return 'demo'
        
        # Default to JEE if unclear
        else:
            return 'jee'
    
    def _extract_time_from_date(self, date: str, scraped_at: str) -> str:
        """
        Extract time from date string or use current time as fallback
        
        Args:
            date: Date string from notification data
            scraped_at: Scraped timestamp as fallback
            
        Returns:
            Formatted time string (HH:MM AM/PM)
        """
        try:
            # If date is provided, try to extract time from it
            if date and date.strip():
                # Try to parse the date and extract time
                parsed_time = self._parse_time_from_date_string(date)
                if parsed_time:
                    return parsed_time
            
            # If no date or couldn't extract time, use scraped_at
            if scraped_at and scraped_at.strip():
                try:
                    # Parse ISO format timestamp
                    dt = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                    return dt.strftime("%I:%M %p")
                except:
                    pass
            
            # Final fallback: current time
            return datetime.now().strftime("%I:%M %p")
            
        except Exception as e:
            self.logger.warning(f"Error extracting time from date '{date}': {e}")
            # Fallback to current time
            return datetime.now().strftime("%I:%M %p")
    
    def _parse_time_from_date_string(self, date_str: str) -> str:
        """
        Parse time from various date string formats
        
        Args:
            date_str: Date string that might contain time
            
        Returns:
            Formatted time string or None if no time found
        """
        import re
        
        # Common time patterns
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)\b',  # 10:30 AM
            r'\b(\d{1,2}):(\d{2})\b',  # 10:30 (assume 24-hour format)
            r'\b(\d{1,2})\s*(AM|PM|am|pm)\b',  # 10 AM
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 3:  # HH:MM AM/PM
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        period = match.group(3).upper()
                        
                        # Convert to 24-hour format for datetime
                        if period == 'PM' and hour != 12:
                            hour += 12
                        elif period == 'AM' and hour == 12:
                            hour = 0
                        
                        dt = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                        return dt.strftime("%I:%M %p")
                        
                    elif len(match.groups()) == 2:  # HH:MM or HH AM/PM
                        if ':' in match.group(0):  # HH:MM format
                            hour = int(match.group(1))
                            minute = int(match.group(2))
                            
                            # Assume 24-hour format, convert to 12-hour
                            dt = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                            return dt.strftime("%I:%M %p")
                        else:  # HH AM/PM format
                            hour = int(match.group(1))
                            period = match.group(2).upper()
                            
                            # Convert to 24-hour format for datetime
                            if period == 'PM' and hour != 12:
                                hour += 12
                            elif period == 'AM' and hour == 12:
                                hour = 0
                            
                            dt = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
                            return dt.strftime("%I:%M %p")
                            
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _determine_location(self, exam_type: str, source: str, title: str, notification_data: Dict[str, Any]) -> str:
        """
        Determine exam location based on available data
        
        Args:
            exam_type: Type of exam
            source: Source of the notification
            title: Title of the notification
            notification_data: Full notification data
            
        Returns:
            Location string
        """
        # First, check if location is explicitly provided in notification data
        explicit_location = notification_data.get('location', '')
        if explicit_location and explicit_location.strip():
            return explicit_location.strip()
        
        # Try to extract location from title or content
        content = notification_data.get('content_summary', notification_data.get('content', ''))
        full_text = f"{title} {content}".lower()
        
        # Common location patterns
        location_patterns = [
            r'\bonline\b',
            r'\bcomputer based\b',
            r'\bcbt\b',
            r'\bpen and paper\b',
            r'\boffline\b',
            r'\bcenters?\b',
            r'\bexam centers?\b',
            r'\bvenue\b',
            r'\blocation\b',
            r'\bconducted\b',
        ]
        
        import re
        for pattern in location_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                # Extract the context around the location mention
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    # Try to get more context
                    start = max(0, match.start() - 20)
                    end = min(len(full_text), match.end() + 20)
                    context = full_text[start:end]
                    
                    # Look for specific location indicators
                    if 'online' in context or 'computer' in context or 'cbt' in context:
                        return "Online"
                    elif 'center' in context or 'venue' in context:
                        # Try to extract city or center name
                        city_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', context)
                        if city_match:
                            return f"Exam Centers ({city_match.group(1)})"
                        else:
                            return "Exam Centers"
        
        # Default location based on exam type
        default_locations = {
            'jee': 'Online (Computer Based Test)',
            'jee_adv': 'Online (Computer Based Test)',
            'gate': 'Online (Computer Based Test)',
            'upsc': 'Offline (Pen and Paper)',
            'neet': 'Offline (Pen and Paper)',
            'cat': 'Online (Computer Based Test)',
            'demo': 'Online'
        }
        
        return default_locations.get(exam_type.lower(), 'Online')
    
    def send_batch_notifications(self, notifications: list) -> Dict[str, Any]:
        """
        Send multiple notifications to webhook API
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            Dictionary with batch results
        """
        results = {
            "total": len(notifications),
            "successful": 0,
            "failed": 0,
            "responses": []
        }
        
        for notification in notifications:
            result = self.send_notification(notification)
            results["responses"].append(result)
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def test_webhook(self) -> Dict[str, Any]:
        """
        Test webhook connectivity with a sample notification
        
        Returns:
            Test result dictionary
        """
        test_notification = {
            "title": "Test Notification",
            "content_summary": "This is a test notification from the exam scraper system.",
            "source": "exam_scraper_test",
            "priority": "low",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "scraped_at": datetime.now().isoformat(),
            "url": "https://example.com"
        }
        
        return self.send_notification(test_notification)


def create_webhook_service() -> WebhookService:
    """Create webhook service with configuration from environment or settings"""
    import os
    
    # Get webhook configuration from environment variables or use defaults
    webhook_url = os.getenv('WEBHOOK_URL', 'https://notification-bot-1757186587.loca.lt/webhook/notification')
    webhook_secret = os.getenv('WEBHOOK_SECRET', 'notif_webhook_2025_secure_key_123')
    
    return WebhookService(webhook_url, webhook_secret)
