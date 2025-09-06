import logging
from abc import ABC, abstractmethod


class AIProcessorWithFallback:
    """AI processor with fallback to multiple providers"""
    
    def __init__(self):
        self.processors = []
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Try to initialize processors in order of preference
        try:
            from .openai_processor import OpenAIProcessor
            self.processors.append(OpenAIProcessor())
            self.logger.info("OpenAI processor initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAI processor: {e}")
        
        try:
            from .claude_processor import ClaudeProcessor
            self.processors.append(ClaudeProcessor())
            self.logger.info("Claude processor initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Claude processor: {e}")
        
        try:
            from .gemini_processor import GeminiProcessor
            self.processors.append(GeminiProcessor())
            self.logger.info("Gemini processor initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Gemini processor: {e}")
        
        if not self.processors:
            self.logger.error("No AI processors available!")
            raise RuntimeError("No AI processors could be initialized")

    def enhance_content(self, updates):
        """Try multiple AI providers as fallback"""
        for processor in self.processors:
            try:
                self.logger.info(f"Trying {processor.__class__.__name__} for content enhancement")
                return processor.enhance_content(updates)
            except Exception as e:
                self.logger.warning(f"{processor.__class__.__name__} failed: {e}")
                continue
        
        # If all AI processors fail, return original content
        self.logger.error("All AI processors failed, returning original content")
        return updates

    def detect_duplicates(self, new_updates, existing_updates):
        """Use the first available processor for duplicate detection"""
        for processor in self.processors:
            try:
                return processor.detect_duplicates(new_updates, existing_updates)
            except Exception as e:
                self.logger.warning(f"{processor.__class__.__name__} duplicate detection failed: {e}")
                continue
        
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
