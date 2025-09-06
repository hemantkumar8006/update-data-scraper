# Scrapers package for exam scraper

from .base_scraper import BaseScraper
from .nta_scraper import NTAScraper
from .jee_advanced_scraper import JEEAdvancedScraper
from .cat_scraper import CATScraper
from .gate_scraper import GATEScraper
from .upsc_scraper import UPSCScraper

__all__ = [
    'BaseScraper',
    'NTAScraper', 
    'JEEAdvancedScraper',
    'CATScraper',
    'GATEScraper',
    'UPSCScraper'
]
