# Scrapers package for exam scraper

from .base_scraper import BaseScraper
from .nta_scraper import NTAScraper
from .jee_advanced_scraper import JEEAdvancedScraper
from .gate_scraper import GATEScraper
from .upsc_scraper import UPSCScraper
from .demo_scraper import DemoScraper

__all__ = [
    'BaseScraper',
    'NTAScraper', 
    'JEEAdvancedScraper',
    'GATEScraper',
    'UPSCScraper',
    'DemoScraper'
]
