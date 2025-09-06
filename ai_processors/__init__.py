# AI processors package for exam scraper

from .base_processor import AIProcessorWithFallback, BaseAIProcessor
from .gemini_processor import GeminiProcessor

__all__ = [
    'AIProcessorWithFallback',
    'BaseAIProcessor',
    'GeminiProcessor'
]
