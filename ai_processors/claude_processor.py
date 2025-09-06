import anthropic
import json
import time
import logging
from config.settings import CLAUDE_API_KEY, AI_BATCH_SIZE, AI_RATE_LIMIT_DELAY


class ClaudeProcessor:
    def __init__(self):
        if not CLAUDE_API_KEY:
            raise ValueError("Claude API key not found. Please set CLAUDE_API_KEY in your environment.")
        
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        self.logger = logging.getLogger(self.__class__.__name__)

    def enhance_content(self, updates):
        """Enhance scraped content with AI analysis"""
        enhanced_updates = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(updates), AI_BATCH_SIZE):
            batch = updates[i:i + AI_BATCH_SIZE]
            try:
                batch_result = self.process_batch(batch)
                enhanced_updates.extend(batch_result)
                
                # Rate limiting delay
                if i + AI_BATCH_SIZE < len(updates):
                    time.sleep(AI_RATE_LIMIT_DELAY)
                    
            except Exception as e:
                self.logger.error(f"Error processing batch with Claude: {e}")
                # Add unprocessed updates as fallback
                enhanced_updates.extend(batch)
                
        return enhanced_updates

    def process_batch(self, batch):
        """Process a batch of updates"""
        enhanced_batch = []
        
        for update in batch:
            try:
                enhanced = self.analyze_single_update(update)
                enhanced_batch.append(enhanced)
            except Exception as e:
                self.logger.error(f"Error processing update with Claude: {e}")
                enhanced_batch.append(update)  # Keep original if AI fails
                
        return enhanced_batch

    def analyze_single_update(self, update):
        """Analyze single update using Claude"""
        prompt = f"""
        Analyze this exam update and provide a detailed summary:
        
        Title: {update['title']}
        Source: {update['source']}
        Original URL: {update.get('url', 'N/A')}
        
        Please provide a JSON response with the following fields:
        1. summary: A clear, concise summary (2-3 sentences)
        2. category: Classification (Application, Result, Admit Card, Exam Date, Notification, etc.)
        3. importance: Importance level (High, Medium, Low)
        4. action_required: Action required by students (if any)
        5. urgency: Urgency level (High, Medium, Low)
        6. key_dates: Any important dates mentioned (if any)
        
        Format as valid JSON only:
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.content[0].text.strip()
            
            # Try to parse JSON response
            try:
                ai_analysis = json.loads(ai_response)
                update.update({
                    'ai_summary': ai_analysis.get('summary', update['content_summary']),
                    'category': ai_analysis.get('category', 'General'),
                    'importance': ai_analysis.get('importance', 'Medium'),
                    'action_required': ai_analysis.get('action_required', 'None'),
                    'urgency': ai_analysis.get('urgency', 'Medium'),
                    'key_dates': ai_analysis.get('key_dates', ''),
                    'processed_by': 'Claude'
                })
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                self.logger.warning("Claude returned non-JSON response, using fallback")
                update.update({
                    'ai_summary': ai_response[:200] if len(ai_response) > 200 else ai_response,
                    'category': 'General',
                    'importance': 'Medium',
                    'action_required': 'None',
                    'urgency': 'Medium',
                    'key_dates': '',
                    'processed_by': 'Claude'
                })
                
        except Exception as e:
            self.logger.error(f"Claude API error: {e}")
            # Fallback to original content
            update.update({
                'ai_summary': update['content_summary'],
                'category': 'General',
                'importance': 'Medium',
                'action_required': 'None',
                'urgency': 'Medium',
                'key_dates': '',
                'processed_by': 'Claude (Failed)'
            })
            
        return update

    def detect_duplicates(self, new_updates, existing_updates):
        """Use AI to detect semantic duplicates"""
        duplicates = []
        unique_updates = []
        
        for new_update in new_updates:
            is_duplicate = False
            for existing_update in existing_updates:
                # Simple similarity check based on title
                similarity = self.calculate_title_similarity(
                    new_update['title'], 
                    existing_update['title']
                )
                if similarity > 0.8:  # 80% similarity threshold
                    duplicates.append({
                        'new_update': new_update,
                        'duplicate_of': existing_update,
                        'similarity': similarity
                    })
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_updates.append(new_update)
        
        return unique_updates, duplicates

    def calculate_title_similarity(self, title1, title2):
        """Calculate similarity between two titles"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
