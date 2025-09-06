import json
import os
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from queue import Queue, Empty
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from .notification_manager import NotificationManager
    from ..utils.webhook_service import create_webhook_service
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.notification_manager import NotificationManager
    from utils.webhook_service import create_webhook_service


class NotificationStatus(Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class QueuedNotification:
    """Represents a notification in the queue"""
    id: str
    notification_data: Dict[str, Any]
    status: NotificationStatus
    created_at: datetime
    attempts: int = 0
    max_attempts: int = 3
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.last_attempt:
            data['last_attempt'] = self.last_attempt.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedNotification':
        """Create from dictionary"""
        data['status'] = NotificationStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_attempt'):
            data['last_attempt'] = datetime.fromisoformat(data['last_attempt'])
        return cls(**data)


class NotificationQueueManager:
    """Manages the notification queue and webhook processing"""
    
    def __init__(self, notification_manager: NotificationManager = None):
        self.notification_manager = notification_manager or NotificationManager()
        self.webhook_service = create_webhook_service()
        self.queue_file = "data/notification_queue.json"
        self.queue = Queue()
        self.processing = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        
        # Load existing queue from file
        self._load_queue()
        
        # Start processing thread
        self._start_processor()
    
    def _load_queue(self) -> None:
        """Load existing queue from file"""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    queue_data = json.load(f)
                
                # Load queued notifications
                for item_data in queue_data.get('queue', []):
                    notification = QueuedNotification.from_dict(item_data)
                    if notification.status in [NotificationStatus.PENDING, NotificationStatus.RETRY]:
                        self.queue.put(notification)
                
                self.logger.info(f"Loaded {self.queue.qsize()} notifications from queue file")
        except Exception as e:
            self.logger.error(f"Error loading queue: {e}")
    
    def _save_queue(self) -> None:
        """Save current queue state to file"""
        try:
            # Get all items from queue (this is a bit tricky with Queue)
            queue_items = []
            temp_queue = Queue()
            
            # Move items to temp queue and collect them
            while not self.queue.empty():
                try:
                    item = self.queue.get_nowait()
                    queue_items.append(item.to_dict())
                    temp_queue.put(item)
                except Empty:
                    break
            
            # Put items back in original queue
            while not temp_queue.empty():
                try:
                    self.queue.put(temp_queue.get_nowait())
                except Empty:
                    break
            
            # Save to file
            queue_data = {
                'queue': queue_items,
                'last_updated': datetime.now().isoformat(),
                'total_items': len(queue_items)
            }
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving queue: {e}")
    
    def add_notification(self, notification_data: Dict[str, Any], exam_type: str = None) -> str:
        """
        Add a notification to the queue
        
        Args:
            notification_data: The notification data
            exam_type: Type of exam (jee, gate, etc.)
            
        Returns:
            Notification ID
        """
        notification_id = f"{exam_type}_{int(time.time() * 1000)}"
        
        queued_notification = QueuedNotification(
            id=notification_id,
            notification_data=notification_data,
            status=NotificationStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.queue.put(queued_notification)
        self.logger.info(f"Added notification {notification_id} to queue")
        
        # Save queue state
        self._save_queue()
        
        return notification_id
    
    def add_batch_notifications(self, notifications: List[Dict[str, Any]], exam_type: str = None) -> List[str]:
        """
        Add multiple notifications to the queue
        
        Args:
            notifications: List of notification data
            exam_type: Type of exam (jee, gate, etc.)
            
        Returns:
            List of notification IDs
        """
        notification_ids = []
        
        for notification_data in notifications:
            notification_id = self.add_notification(notification_data, exam_type)
            notification_ids.append(notification_id)
        
        self.logger.info(f"Added {len(notifications)} notifications to queue")
        return notification_ids
    
    def _start_processor(self) -> None:
        """Start the queue processing thread"""
        if not self.processing:
            self.processing = True
            self.processor_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.processor_thread.start()
            self.logger.info("Notification queue processor started")
    
    def _process_queue(self) -> None:
        """Process notifications in the queue"""
        while self.processing:
            try:
                # Get notification from queue (with timeout)
                notification = self.queue.get(timeout=5)
                
                # Process the notification
                self._process_notification(notification)
                
                # Mark task as done
                self.queue.task_done()
                
            except Empty:
                # No notifications in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error processing queue: {e}")
                time.sleep(1)  # Wait before retrying
    
    def _process_notification(self, notification: QueuedNotification) -> None:
        """
        Process a single notification
        
        Args:
            notification: The queued notification to process
        """
        try:
            # Update status to sending
            notification.status = NotificationStatus.SENDING
            notification.attempts += 1
            notification.last_attempt = datetime.now()
            
            self.logger.info(f"Processing notification {notification.id} (attempt {notification.attempts})")
            
            # Send webhook
            webhook_result = self.webhook_service.send_notification(notification.notification_data)
            
            if webhook_result['success']:
                # Success
                notification.status = NotificationStatus.SENT
                notification.error_message = None
                self.logger.info(f"✅ Notification {notification.id} sent successfully")
            else:
                # Failed
                notification.error_message = webhook_result.get('error', 'Unknown error')
                
                if notification.attempts < notification.max_attempts:
                    # Retry
                    notification.status = NotificationStatus.RETRY
                    self.queue.put(notification)  # Put back in queue for retry
                    self.logger.warning(f"⚠️  Notification {notification.id} failed, will retry (attempt {notification.attempts}/{notification.max_attempts})")
                else:
                    # Max attempts reached
                    notification.status = NotificationStatus.FAILED
                    self.logger.error(f"❌ Notification {notification.id} failed after {notification.max_attempts} attempts")
            
            # Save queue state after processing
            self._save_queue()
            
        except Exception as e:
            self.logger.error(f"Error processing notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            self._save_queue()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            # Count items by status
            status_counts = {
                'pending': 0,
                'sending': 0,
                'sent': 0,
                'failed': 0,
                'retry': 0
            }
            
            # This is a bit tricky with Queue, we'll estimate based on file
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    queue_data = json.load(f)
                
                for item_data in queue_data.get('queue', []):
                    status = item_data.get('status', 'pending')
                    if status in status_counts:
                        status_counts[status] += 1
            
            return {
                'queue_size': self.queue.qsize(),
                'status_counts': status_counts,
                'processing': self.processing,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting queue status: {e}")
            return {
                'queue_size': 0,
                'status_counts': {},
                'processing': False,
                'error': str(e)
            }
    
    def clear_queue(self) -> None:
        """Clear all items from the queue"""
        try:
            # Clear the queue
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Empty:
                    break
            
            # Clear the file
            if os.path.exists(self.queue_file):
                os.remove(self.queue_file)
            
            self.logger.info("Queue cleared")
        except Exception as e:
            self.logger.error(f"Error clearing queue: {e}")
    
    def stop_processing(self) -> None:
        """Stop the queue processing"""
        self.processing = False
        self.logger.info("Queue processing stopped")


def create_notification_queue(notification_manager: NotificationManager = None) -> NotificationQueueManager:
    """Create a notification queue manager instance"""
    return NotificationQueueManager(notification_manager)


if __name__ == '__main__':
    # Test the queue system
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    # Create queue manager
    queue_manager = create_notification_queue()
    
    # Add test notifications
    test_notifications = [
        {
            "title": "Test Notification 1",
            "content": "This is a test notification",
            "exam_type": "jee",
            "source": "test",
            "priority": "medium"
        },
        {
            "title": "Test Notification 2", 
            "content": "This is another test notification",
            "exam_type": "gate",
            "source": "test",
            "priority": "high"
        }
    ]
    
    # Add notifications to queue
    notification_ids = queue_manager.add_batch_notifications(test_notifications, "test")
    print(f"Added {len(notification_ids)} test notifications to queue")
    
    # Wait for processing
    time.sleep(10)
    
    # Get status
    status = queue_manager.get_queue_status()
    print(f"Queue status: {status}")
    
    # Stop processing
    queue_manager.stop_processing()
