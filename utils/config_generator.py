"""
Configuration Generator - Helps users create scraper configurations easily
"""

import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import logging


class ConfigGenerator:
    """
    Helps users generate scraper configurations by analyzing website structure
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Any]:
        """Load scraper templates"""
        try:
            with open('config/scraper_templates.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            return {"templates": {}, "exam_specific_templates": {}}
    
    def generate_config_from_url(self, url: str, exam_type: str = None, 
                                custom_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Generate scraper configuration by analyzing a website URL
        """
        try:
            # Fetch and analyze the website
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Analyze page structure
            analysis = self._analyze_page_structure(soup)
            
            # Generate configuration
            config = self._generate_config_from_analysis(
                url, analysis, exam_type, custom_keywords
            )
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to generate config from URL {url}: {e}")
            return self._get_fallback_config(url, exam_type, custom_keywords)
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze the structure of a webpage to suggest selectors"""
        analysis = {
            'potential_containers': [],
            'potential_titles': [],
            'potential_dates': [],
            'potential_links': [],
            'suggested_strategy': 'standard'
        }
        
        # Find potential news/announcement containers
        container_selectors = [
            '.news', '.announcement', '.update', '.post', '.item',
            '.notification', '.notice', '.alert', '.ticker', '.marquee',
            '.latest', '.recent', '.whats-new', '.updates'
        ]
        
        for selector in container_selectors:
            elements = soup.select(selector)
            if elements:
                analysis['potential_containers'].append({
                    'selector': selector,
                    'count': len(elements),
                    'sample_text': elements[0].get_text(strip=True)[:100] if elements else ""
                })
        
        # Find potential title elements
        title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.headline', '.announcement-title']
        for selector in title_selectors:
            elements = soup.select(selector)
            if elements:
                analysis['potential_titles'].append({
                    'selector': selector,
                    'count': len(elements),
                    'sample_text': elements[0].get_text(strip=True)[:100] if elements else ""
                })
        
        # Find potential date elements
        date_selectors = ['.date', '.publish-date', '.timestamp', '.time', '.published']
        for selector in date_selectors:
            elements = soup.select(selector)
            if elements:
                analysis['potential_dates'].append({
                    'selector': selector,
                    'count': len(elements),
                    'sample_text': elements[0].get_text(strip=True)[:50] if elements else ""
                })
        
        # Determine best strategy
        if len(analysis['potential_containers']) > 1:
            analysis['suggested_strategy'] = 'multi_section'
        elif any('ticker' in container['selector'] or 'marquee' in container['selector'] 
                for container in analysis['potential_containers']):
            analysis['suggested_strategy'] = 'ticker_marquee'
        
        return analysis
    
    def _generate_config_from_analysis(self, url: str, analysis: Dict[str, Any], 
                                     exam_type: str = None, 
                                     custom_keywords: List[str] = None) -> Dict[str, Any]:
        """Generate configuration from page analysis"""
        
        # Start with base template
        if exam_type and exam_type in self.templates['exam_specific_templates']:
            config = self.templates['exam_specific_templates'][exam_type].copy()
        else:
            config = self.templates['templates']['standard_news_site'].copy()
        
        # Update with analyzed data
        config['url'] = url
        config['name'] = f"Auto-generated for {url}"
        
        # Update selectors based on analysis
        if analysis['potential_containers']:
            best_container = max(analysis['potential_containers'], key=lambda x: x['count'])
            config['selectors']['news_container'] = best_container['selector']
        
        if analysis['potential_titles']:
            best_title = max(analysis['potential_titles'], key=lambda x: x['count'])
            config['selectors']['title'] = best_title['selector']
        
        if analysis['potential_dates']:
            best_date = max(analysis['potential_dates'], key=lambda x: x['count'])
            config['selectors']['date'] = best_date['selector']
        
        # Update strategy
        config['parsing_strategy'] = analysis['suggested_strategy']
        
        # Update keywords
        if custom_keywords:
            config['keywords'] = custom_keywords
        elif exam_type:
            config['keywords'] = self._get_default_keywords_for_exam(exam_type)
        
        # Set exam type
        if exam_type:
            config['exam_type'] = exam_type
        
        return config
    
    def _get_fallback_config(self, url: str, exam_type: str = None, 
                           custom_keywords: List[str] = None) -> Dict[str, Any]:
        """Get fallback configuration when analysis fails"""
        config = {
            "name": f"Fallback config for {url}",
            "url": url,
            "parsing_strategy": "standard",
            "selectors": {
                "news_container": ".news, .announcement, .update, .post, .item",
                "title": "h1, h2, h3, .title, .headline",
                "date": ".date, .publish-date, .timestamp",
                "link": "a"
            },
            "keywords": custom_keywords or ["exam", "notification", "result"],
            "priority": "medium",
            "enabled": True
        }
        
        if exam_type:
            config['exam_type'] = exam_type
            config['keywords'] = self._get_default_keywords_for_exam(exam_type)
        
        return config
    
    def _get_default_keywords_for_exam(self, exam_type: str) -> List[str]:
        """Get default keywords for specific exam types"""
        keyword_map = {
            'jee_main': ['jee', 'main', 'exam', 'admit card', 'result', 'application', 'registration', 'notification'],
            'jee_advanced': ['jee', 'advanced', 'exam', 'registration', 'result', 'admit card', 'notification'],
            'gate': ['gate', 'exam', 'application', 'result', 'admit card', 'registration', 'notification'],
            'upsc': ['upsc', 'civil services', 'exam', 'notification', 'result', 'admit card', 'application'],
            'neet': ['neet', 'exam', 'admit card', 'result', 'application', 'registration', 'notification'],
            'cat': ['cat', 'exam', 'admit card', 'result', 'application', 'registration', 'notification']
        }
        
        return keyword_map.get(exam_type, ['exam', 'notification', 'result'])
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a scraper configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Required fields
        required_fields = ['name', 'url', 'selectors']
        for field in required_fields:
            if field not in config:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        # Validate selectors
        if 'selectors' in config:
            required_selectors = ['news_container', 'title']
            for selector in required_selectors:
                if selector not in config['selectors']:
                    validation_result['errors'].append(f"Missing required selector: {selector}")
                    validation_result['valid'] = False
        
        # Validate URL
        if 'url' in config:
            if not config['url'].startswith(('http://', 'https://', 'file://')):
                validation_result['errors'].append("Invalid URL format")
                validation_result['valid'] = False
        
        # Check for common issues
        if 'keywords' in config and not config['keywords']:
            validation_result['warnings'].append("No keywords specified - all content will be considered relevant")
        
        if 'parsing_strategy' not in config:
            validation_result['suggestions'].append("Consider specifying parsing_strategy for better performance")
        
        return validation_result
    
    def test_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a configuration by running a sample scrape"""
        from scrapers.configurable_scraper import ConfigurableScraper
        
        test_result = {
            'success': False,
            'updates_found': 0,
            'errors': [],
            'sample_updates': []
        }
        
        try:
            scraper = ConfigurableScraper(config)
            updates = scraper.scrape()
            
            test_result['success'] = True
            test_result['updates_found'] = len(updates)
            test_result['sample_updates'] = updates[:3]  # First 3 updates as samples
            
        except Exception as e:
            test_result['errors'].append(str(e))
        
        return test_result
    
    def get_template_suggestions(self, exam_type: str = None) -> List[Dict[str, Any]]:
        """Get template suggestions based on exam type"""
        suggestions = []
        
        if exam_type and exam_type in self.templates['exam_specific_templates']:
            suggestions.append({
                'name': f"{exam_type.upper()} Specific Template",
                'template': self.templates['exam_specific_templates'][exam_type],
                'description': f"Template specifically designed for {exam_type.upper()} websites"
            })
        
        # Add general templates
        for name, template in self.templates['templates'].items():
            suggestions.append({
                'name': template['name'],
                'template': template,
                'description': template['description']
            })
        
        return suggestions
