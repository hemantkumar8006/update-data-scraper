# Migration Guide: From Individual Scrapers to Configurable System

## Overview

This guide helps you migrate from the old system with individual scraper files to the new configurable system that can handle any number of exams without code changes.

## Migration Steps

### Step 1: Backup Current System

Before starting the migration, create a backup of your current system:

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

# Backup current configurations
cp config/websites.json backups/$(date +%Y%m%d_%H%M%S)/

# Backup current scrapers
cp -r scrapers/ backups/$(date +%Y%m%d_%H%M%S)/
```

### Step 2: Install New Components

The new system includes several new components:

1. **ConfigurableScraper**: `scrapers/configurable_scraper.py`
2. **Configuration Generator**: `utils/config_generator.py`
3. **Plugin System**: `plugins/` directory
4. **Configuration API**: `api/config_api.py`
5. **Web Interface**: `templates/config_interface.html`

### Step 3: Convert Existing Scrapers

#### Example: Converting NTA Scraper

**Old System (nta_scraper.py):**

```python
class NTAScraper(BaseScraper):
    def scrape(self):
        response = self.fetch_page(self.config['url'])
        updates = self.parse_content(response.text)

        # Additional NTA-specific parsing
        soup = BeautifulSoup(response.text, 'lxml')

        # Parse news ticker
        ticker_updates = self.parse_news_ticker(soup)
        updates.extend(ticker_updates)

        # Parse scrollable notices
        notices_updates = self.parse_scrollable_notices(soup)
        updates.extend(notices_updates)

        return updates
```

**New System (Configuration):**

```json
{
  "name": "JEE Main NTA",
  "url": "https://jeemain.nta.nic.in/",
  "scraper_class": "ConfigurableScraper",
  "parsing_strategy": "multi_section",
  "sections": [
    {
      "name": "news_ticker",
      "container_selector": ".newsticker .slides li",
      "selectors": {
        "title": "",
        "date": "",
        "link": "a"
      }
    },
    {
      "name": "scrollable_notices",
      "container_selector": ".scrollable-notices a, .notice-item",
      "selectors": {
        "title": "",
        "date": "",
        "link": ""
      }
    }
  ],
  "keywords": [
    "jee",
    "main",
    "exam",
    "admit card",
    "result",
    "application",
    "registration",
    "notification"
  ],
  "enabled": true,
  "priority": "high",
  "exam_type": "jee_main"
}
```

#### Example: Converting GATE Scraper

**Old System (gate_scraper.py):**

```python
class GATEScraper(BaseScraper):
    def scrape(self):
        response = self.fetch_page(self.config['url'])
        updates = self.parse_content(response.text)

        soup = BeautifulSoup(response.text, 'lxml')

        # Parse ticker section
        ticker_updates = self.parse_ticker_section(soup)
        updates.extend(ticker_updates)

        # Parse important dates
        dates_updates = self.parse_important_dates(soup)
        updates.extend(dates_updates)

        return updates
```

**New System (Configuration):**

```json
{
  "name": "GATE 2026",
  "url": "https://gate2026.iitg.ac.in/",
  "scraper_class": "ConfigurableScraper",
  "parsing_strategy": "multi_section",
  "sections": [
    {
      "name": "ticker",
      "container_selector": ".ticker .news .news-content",
      "selectors": {
        "title": "",
        "date": "",
        "link": ""
      }
    },
    {
      "name": "important_dates",
      "container_selector": ".imp-dates-item li",
      "selectors": {
        "title": "",
        "date": ".text-warning",
        "link": ""
      }
    },
    {
      "name": "highlights",
      "container_selector": ".highlight-item",
      "selectors": {
        "title": ".title a",
        "date": "",
        "link": ".title a"
      }
    }
  ],
  "keywords": [
    "gate",
    "exam",
    "application",
    "result",
    "admit card",
    "registration",
    "notification"
  ],
  "enabled": true,
  "priority": "high",
  "exam_type": "gate"
}
```

### Step 4: Update Server Configuration

Update your main server to use the new configurable system:

**Old System (main.py):**

```python
from scrapers import (
    NTAScraper, JEEAdvancedScraper,
    GATEScraper, UPSCScraper, DemoScraper
)

def init_scrapers(self):
    scraper_classes = {
        'NTAScraper': NTAScraper,
        'JEEAdvancedScraper': JEEAdvancedScraper,
        'GATEScraper': GATEScraper,
        'UPSCScraper': UPSCScraper,
        'DemoScraper': DemoScraper
    }

    for website in self.website_configs['websites']:
        scraper_class = scraper_classes.get(website['scraper_class'])
        if scraper_class:
            self.scrapers[website['name']] = scraper_class(website)
```

**New System (main.py):**

```python
from scrapers.configurable_scraper import ConfigurableScraper

def init_scrapers(self):
    for website in self.website_configs['websites']:
        # All scrapers now use ConfigurableScraper
        scraper = ConfigurableScraper(website)
        self.scrapers[website['name']] = scraper
```

### Step 5: Test the Migration

1. **Test Individual Configurations:**

   ```python
   from utils.config_generator import ConfigGenerator

   config_generator = ConfigGenerator()
   test_result = config_generator.test_config(your_config)
   print(f"Test successful: {test_result['success']}")
   print(f"Updates found: {test_result['updates_found']}")
   ```

2. **Test the Full System:**

   ```python
   from mcp_server.configurable_server import ConfigurableExamScrapingServer

   server = ConfigurableExamScrapingServer()
   result = server.run_single_scrape()
   print(f"Scraping completed: {result['new_updates_count']} new updates")
   ```

### Step 6: Gradual Migration Strategy

#### Phase 1: Parallel Operation

- Keep old scrapers running
- Add new exams using configurable system
- Test new system thoroughly

#### Phase 2: Migration

- Convert existing scrapers to configurations
- Test each conversion
- Update server to use new system

#### Phase 3: Cleanup

- Remove old scraper files
- Update documentation
- Train users on new system

### Step 7: Using the Web Interface

1. **Access the Configuration Interface:**

   - Navigate to `http://localhost:5000/config`
   - Use the web interface to manage configurations

2. **Add New Exams:**

   - Use "Quick Setup" for simple websites
   - Use "Advanced Configuration" for complex sites
   - Choose from templates for common patterns

3. **Test Configurations:**
   - Use the built-in testing feature
   - Validate configurations before saving
   - Monitor scraping results

## Common Migration Issues

### Issue 1: Selector Changes

**Problem:** Website structure has changed since original scraper was written.

**Solution:**

1. Use browser dev tools to inspect current structure
2. Update selectors in configuration
3. Test with new selectors

### Issue 2: Complex Parsing Logic

**Problem:** Original scraper has complex custom logic.

**Solution:**

1. Create a custom plugin for complex logic
2. Use the plugin in configuration
3. Test the plugin thoroughly

### Issue 3: Performance Issues

**Problem:** New system is slower than old scrapers.

**Solution:**

1. Optimize selectors (be more specific)
2. Reduce scraping frequency
3. Use caching where appropriate

### Issue 4: Missing Features

**Problem:** Some features from old scrapers are missing.

**Solution:**

1. Identify missing features
2. Implement in ConfigurableScraper or create plugin
3. Update configuration to use new features

## Best Practices for Migration

### 1. Start Small

- Begin with simple scrapers
- Test thoroughly before migrating complex ones
- Use the web interface for easy testing

### 2. Document Changes

- Keep track of configuration changes
- Document any custom plugins
- Maintain migration notes

### 3. Test Extensively

- Test each configuration individually
- Test the full system after migration
- Monitor for any issues

### 4. Gradual Rollout

- Don't migrate everything at once
- Keep old system as backup
- Have rollback plan ready

### 5. User Training

- Train users on new web interface
- Provide documentation and examples
- Offer support during transition

## Rollback Plan

If you need to rollback to the old system:

1. **Restore Backup:**

   ```bash
   cp backups/YYYYMMDD_HHMMSS/websites.json config/
   cp -r backups/YYYYMMDD_HHMMSS/scrapers/ ./
   ```

2. **Update Server:**

   - Revert main.py to use old scraper classes
   - Restart the server

3. **Verify Functionality:**
   - Test that old scrapers work
   - Check that data is being collected
   - Monitor for any issues

## Post-Migration Tasks

### 1. Cleanup

- Remove old scraper files
- Update documentation
- Clean up unused code

### 2. Optimization

- Monitor performance
- Optimize configurations
- Update scraping schedules

### 3. Training

- Train users on new system
- Provide updated documentation
- Set up support processes

### 4. Monitoring

- Monitor scraping success rates
- Track performance metrics
- Watch for website changes

## Conclusion

The migration to the configurable system provides significant benefits in terms of scalability, maintainability, and ease of use. While the migration process requires careful planning and testing, the long-term benefits make it worthwhile.

The new system eliminates the need for individual scraper files, making it easy to add new exams without any programming knowledge. The web interface and configuration templates make the system accessible to non-technical users while still providing the flexibility to handle complex websites through custom plugins.

By following this migration guide and best practices, you can successfully transition to the new system while maintaining the functionality of your existing scrapers.
