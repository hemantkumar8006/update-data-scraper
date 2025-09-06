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
                "X-Webhook-Secret": "notif_webhook_2025_secure_key_123"
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
        notification_data.get('url', '')
        date = notification_data.get('date', '')
        notification_data.get('scraped_at', '')
        
        # Determine exam type from source or title
        exam_type = self._determine_exam_type(notification_data)
        
        # Format exam name based on exam type
        exam_name_mapping = {
            'jee': 'JEE Main',
            'jee_adv': 'JEE Advanced', 
            'gate': 'GATE',
            'upsc': 'UPSC Civil Services',
            'cat': 'CAT',
            'demo': 'Demo Notification'
        }
        exam_name = exam_name_mapping.get(exam_type.lower(), exam_type.upper())
        
        # Create payload matching the bot's expected format
        # Only include the exact fields the bot expects
        payload = {
            "title": title,
            "content": content,
            "notificationType": "exam_updates",
            "metadata": {
                "examName": exam_name,
                "examDate": date,
                "examTime": "10:00 AM",  # Default time
                "location": "Online",     # Default location
                "priority": priority,
                "source": source
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
        
        # Check for JEE Main (or any JEE that's not Advanced)
        elif ('jee' in source or 'jee' in title or 'nta' in source):
            return 'jee'
        
        # Check for demo notifications
        elif ('demo' in source or 'demo' in title or 'bot testing' in source):
            return 'demo'
        
        # Default to JEE if unclear
        else:
            return 'jee'
    
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
    webhook_url = "https://rare-walls-pay.loca.lt/webhook/notification"
    webhook_secret = "notif_webhook_2025_secure_key_123"
    
    return WebhookService(webhook_url, webhook_secret)
