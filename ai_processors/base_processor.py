import logging
from abc import ABC, abstractmethod


class AIProcessorWithFallback:
    """AI processor using Gemini only"""
    
    def __init__(self):
        self.processor = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize Gemini processor
        try:
            from .gemini_processor import GeminiProcessor
            self.processor = GeminiProcessor()
            self.logger.info("Gemini processor initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini processor: {e}")
            raise RuntimeError("Gemini processor could not be initialized")

    def enhance_content(self, updates):
        """Enhance content using Gemini processor"""
        try:
            self.logger.info("Using Gemini for content enhancement")
            return self.processor.enhance_content(updates)
        except Exception as e:
            self.logger.error(f"Gemini processor failed: {e}")
            # Return original content if AI processing fails
            return updates

    def detect_duplicates(self, new_updates, existing_updates):
        """Use Gemini processor for duplicate detection"""
        try:
            return self.processor.detect_duplicates(new_updates, existing_updates)
        except Exception as e:
            self.logger.warning(f"Gemini duplicate detection failed: {e}")
            # Fallback to simple duplicate detection
            return self.simple_duplicate_detection(new_updates, existing_updates)

    def simple_duplicate_detection(self, new_updates, existing_updates):
        """Simple duplicate detection based on content hash"""
        duplicates = []
        unique_updates = []
        
        existing_hashes = {update.get('content_hash') for update in existing_updates}
        
        for new_update in new_updates:
            if new_update.get('content_hash') in existing_hashes:
                duplicates.append({
                    'new_update': new_update,
                    'duplicate_of': 'Hash match',
                    'similarity': 1.0
                })
            else:
                unique_updates.append(new_update)
        
        return unique_updates, duplicates


class BaseAIProcessor(ABC):
    """Base class for AI processors"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def enhance_content(self, updates):
        """Enhance scraped content with AI analysis"""
        pass

    @abstractmethod
    def analyze_single_update(self, update):
        """Analyze single update using AI"""
        pass

    @abstractmethod
    def detect_duplicates(self, new_updates, existing_updates):
        """Detect semantic duplicates"""
        pass
