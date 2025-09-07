"""
Configuration API - REST endpoints for managing scraper configurations
"""

from flask import Blueprint, request, jsonify
import json
import logging
from typing import Dict, Any
from utils.config_generator import ConfigGenerator
from scrapers.configurable_scraper import ConfigurableScraper

# Create blueprint
config_api = Blueprint('config_api', __name__)
logger = logging.getLogger(__name__)

# Initialize config generator
config_generator = ConfigGenerator()


@config_api.route('/api/generate-config', methods=['POST'])
def generate_config():
    """Generate scraper configuration from URL"""
    try:
        data = request.get_json()
        
        url = data.get('url')
        exam_type = data.get('exam_type')
        name = data.get('name')
        keywords = data.get('keywords', [])
        
        if not url or not name:
            return jsonify({
                'success': False,
                'error': 'URL and name are required'
            }), 400
        
        # Generate configuration
        config = config_generator.generate_config_from_url(
            url=url,
            exam_type=exam_type,
            custom_keywords=keywords
        )
        
        # Update with provided name
        config['name'] = name
        
        # Validate configuration
        validation = config_generator.validate_config(config)
        
        return jsonify({
            'success': True,
            'config': config,
            'validation': validation
        })
        
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/test-config', methods=['POST'])
def test_config():
    """Test a scraper configuration"""
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuration is required'
            }), 400
        
        # Test configuration
        test_result = config_generator.test_config(config)
        
        return jsonify(test_result)
        
    except Exception as e:
        logger.error(f"Error testing config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/save-config', methods=['POST'])
def save_config():
    """Save a scraper configuration"""
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuration is required'
            }), 400
        
        # Validate configuration
        validation = config_generator.validate_config(config)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'validation': validation
            }), 400
        
        # Load existing configurations
        try:
            with open('config/websites.json', 'r') as f:
                websites_config = json.load(f)
        except FileNotFoundError:
            websites_config = {'websites': []}
        
        # Check if configuration with same name already exists
        existing_names = [w['name'] for w in websites_config['websites']]
        if config['name'] in existing_names:
            return jsonify({
                'success': False,
                'error': 'Configuration with this name already exists'
            }), 400
        
        # Add new configuration
        config['enabled'] = True
        config['scraper_class'] = 'ConfigurableScraper'
        websites_config['websites'].append(config)
        
        # Save updated configuration
        with open('config/websites.json', 'w') as f:
            json.dump(websites_config, f, indent=2)
        
        logger.info(f"Saved new configuration: {config['name']}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/configs', methods=['GET'])
def get_configs():
    """Get all existing configurations"""
    try:
        with open('config/websites.json', 'r') as f:
            websites_config = json.load(f)
        
        # Filter out demo configurations for display
        configs = [
            config for config in websites_config['websites']
            if not config.get('name', '').lower().startswith('demo')
        ]
        
        return jsonify(configs)
        
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        logger.error(f"Error loading configs: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@config_api.route('/api/configs/<config_name>', methods=['GET'])
def get_config(config_name):
    """Get specific configuration by name"""
    try:
        with open('config/websites.json', 'r') as f:
            websites_config = json.load(f)
        
        config = next(
            (c for c in websites_config['websites'] if c['name'] == config_name),
            None
        )
        
        if not config:
            return jsonify({
                'error': 'Configuration not found'
            }), 404
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error loading config {config_name}: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@config_api.route('/api/configs/<config_name>', methods=['PUT'])
def update_config(config_name):
    """Update existing configuration"""
    try:
        updated_config = request.get_json()
        
        if not updated_config:
            return jsonify({
                'success': False,
                'error': 'Configuration is required'
            }), 400
        
        # Load existing configurations
        with open('config/websites.json', 'r') as f:
            websites_config = json.load(f)
        
        # Find and update configuration
        config_found = False
        for i, config in enumerate(websites_config['websites']):
            if config['name'] == config_name:
                # Preserve some fields
                updated_config['enabled'] = config.get('enabled', True)
                updated_config['scraper_class'] = 'ConfigurableScraper'
                websites_config['websites'][i] = updated_config
                config_found = True
                break
        
        if not config_found:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        # Validate updated configuration
        validation = config_generator.validate_config(updated_config)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'validation': validation
            }), 400
        
        # Save updated configuration
        with open('config/websites.json', 'w') as f:
            json.dump(websites_config, f, indent=2)
        
        logger.info(f"Updated configuration: {config_name}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating config {config_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/configs/<config_name>', methods=['DELETE'])
def delete_config(config_name):
    """Delete configuration"""
    try:
        # Load existing configurations
        with open('config/websites.json', 'r') as f:
            websites_config = json.load(f)
        
        # Remove configuration
        original_count = len(websites_config['websites'])
        websites_config['websites'] = [
            config for config in websites_config['websites']
            if config['name'] != config_name
        ]
        
        if len(websites_config['websites']) == original_count:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        # Save updated configuration
        with open('config/websites.json', 'w') as f:
            json.dump(websites_config, f, indent=2)
        
        logger.info(f"Deleted configuration: {config_name}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting config {config_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/configs/<config_name>/toggle', methods=['POST'])
def toggle_config(config_name):
    """Enable/disable configuration"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        # Load existing configurations
        with open('config/websites.json', 'r') as f:
            websites_config = json.load(f)
        
        # Find and update configuration
        config_found = False
        for config in websites_config['websites']:
            if config['name'] == config_name:
                config['enabled'] = enabled
                config_found = True
                break
        
        if not config_found:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        # Save updated configuration
        with open('config/websites.json', 'w') as f:
            json.dump(websites_config, f, indent=2)
        
        status = "enabled" if enabled else "disabled"
        logger.info(f"{status.capitalize()} configuration: {config_name}")
        
        return jsonify({
            'success': True,
            'message': f'Configuration {status} successfully'
        })
        
    except Exception as e:
        logger.error(f"Error toggling config {config_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/templates', methods=['GET'])
def get_templates():
    """Get available configuration templates"""
    try:
        templates = config_generator.get_template_suggestions()
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@config_api.route('/api/validate-config', methods=['POST'])
def validate_config():
    """Validate a configuration"""
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuration is required'
            }), 400
        
        validation = config_generator.validate_config(config)
        
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Error validating config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/api/analyze-url', methods=['POST'])
def analyze_url():
    """Analyze URL structure without generating full config"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        # Generate basic analysis
        config = config_generator.generate_config_from_url(url)
        
        # Return analysis results
        return jsonify({
            'success': True,
            'analysis': {
                'suggested_strategy': config.get('parsing_strategy', 'standard'),
                'suggested_selectors': config.get('selectors', {}),
                'suggested_keywords': config.get('keywords', []),
                'exam_type': config.get('exam_type')
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing URL: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
