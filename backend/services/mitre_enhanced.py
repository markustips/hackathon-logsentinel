"""Enhanced MITRE ATT&CK mapping service with web search."""
import re
from typing import List, Dict, Any, Optional
import logging
from services.mitre import MitreMapper

logger = logging.getLogger(__name__)


class EnhancedMitreMapper(MitreMapper):
    """Enhanced MITRE mapper with web search capabilities."""

    def __init__(self, use_web_search: bool = True):
        """
        Initialize enhanced mapper.

        Args:
            use_web_search: Whether to use web search for validation
        """
        super().__init__()
        self.use_web_search = use_web_search

    async def search_mitre_technique(self, technique_id: str, description: str = "") -> Optional[Dict[str, Any]]:
        """
        Search MITRE ATT&CK online for technique details.

        Args:
            technique_id: MITRE technique ID (e.g., T1110)
            description: Additional context for search

        Returns:
            Enhanced technique details from web search
        """
        if not self.use_web_search:
            return None

        try:
            # Import here to avoid dependency issues if not available
            from anthropic import Anthropic
            import os

            client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            # Construct search query
            search_query = f"MITRE ATT&CK {technique_id}"
            if description:
                search_query += f" {description}"

            # Use Claude with web search
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=[{
                    "type": "web_search_tool",
                    "name": "web_search",
                    "description": "Search the web for MITRE ATT&CK technique details"
                }],
                messages=[{
                    "role": "user",
                    "content": f"Search for MITRE ATT&CK technique {technique_id}. Return: name, tactic, description, detection methods, and examples. Format as JSON."
                }]
            )

            # Parse response
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        # Extract JSON from response
                        text = block.text
                        # Try to parse structured data
                        import json
                        try:
                            data = json.loads(text)
                            return {
                                'id': technique_id,
                                'name': data.get('name', 'Unknown'),
                                'tactic': data.get('tactic', 'Unknown'),
                                'description': data.get('description', ''),
                                'detection': data.get('detection', []),
                                'examples': data.get('examples', []),
                                'url': f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/"
                            }
                        except json.JSONDecodeError:
                            # Fall back to text parsing
                            logger.debug(f"Could not parse JSON for {technique_id}, using text")

            return None

        except Exception as e:
            logger.warning(f"Web search for {technique_id} failed: {e}")
            return None

    async def validate_technique_mapping(self, message: str, technique_id: str) -> bool:
        """
        Validate if a technique mapping is accurate using web search.

        Args:
            message: Log message
            technique_id: Proposed MITRE technique ID

        Returns:
            True if mapping is validated, False otherwise
        """
        if not self.use_web_search:
            return True  # Trust local patterns if web search disabled

        try:
            # Get technique details from web
            details = await self.search_mitre_technique(technique_id, message[:200])

            if not details:
                return True  # Fall back to local pattern if web search fails

            # Check if message keywords match technique description
            message_lower = message.lower()
            description_lower = details.get('description', '').lower()

            # Extract key terms from message
            message_terms = set(re.findall(r'\b\w{4,}\b', message_lower))
            description_terms = set(re.findall(r'\b\w{4,}\b', description_lower))

            # Calculate overlap
            if not description_terms:
                return True

            overlap = len(message_terms & description_terms) / len(description_terms)

            # Threshold: at least 10% term overlap
            return overlap >= 0.1

        except Exception as e:
            logger.warning(f"Validation for {technique_id} failed: {e}")
            return True  # Fall back to trusting local pattern

    async def map_message_enhanced(self, message: str, validate: bool = True) -> List[Dict[str, Any]]:
        """
        Map a log message to MITRE ATT&CK techniques with web search validation.

        Args:
            message: Log message text
            validate: Whether to validate mappings with web search

        Returns:
            List of matched and validated MITRE techniques
        """
        # Get initial mappings from pattern matching
        techniques = self.map_message(message)

        if not self.use_web_search or not validate:
            return techniques

        # Validate each technique
        validated = []
        for technique in techniques:
            is_valid = await self.validate_technique_mapping(message, technique['id'])
            if is_valid:
                validated.append(technique)
            else:
                logger.info(f"Filtered out {technique['id']} - failed web validation")

        return validated

    async def enrich_techniques_with_web_data(self, techniques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich technique details with web search data.

        Args:
            techniques: List of techniques to enrich

        Returns:
            Enriched techniques with additional details
        """
        if not self.use_web_search:
            return techniques

        enriched = []
        for technique in techniques:
            # Get web data
            web_data = await self.search_mitre_technique(technique['id'])

            if web_data:
                # Merge with existing data
                enriched_technique = {**technique, **web_data}
            else:
                enriched_technique = technique

            enriched.append(enriched_technique)

        return enriched

    def get_technique_summary(self, technique: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of a MITRE technique.

        Args:
            technique: Technique details

        Returns:
            Formatted summary
        """
        summary_parts = [
            f"**{technique['id']} - {technique['name']}**",
            f"Tactic: {technique['tactic']}",
            f"URL: {technique['url']}"
        ]

        if 'description' in technique:
            summary_parts.append(f"Description: {technique['description'][:200]}...")

        if 'detection' in technique and technique['detection']:
            summary_parts.append(f"Detection: {', '.join(technique['detection'][:3])}")

        return '\n'.join(summary_parts)
