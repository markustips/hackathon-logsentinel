"""Update tools.py to use enhanced MITRE mapper."""

# Read file
with open('agents/tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace import
content = content.replace(
    'from services.mitre import MitreMapper',
    'from services.mitre_web_enhanced import WebEnhancedMitreMapper'
)

# Replace initialization
content = content.replace(
    'self.mapper = MitreMapper()',
    'self.mapper = WebEnhancedMitreMapper(use_web_api=True)'
)

# Add method for enhanced mapping
if 'def map_to_mitre_enhanced' not in content:
    # Find the position after map_to_mitre method
    insert_pos = content.find('    def get_timeline(self, file_id: str)')

    if insert_pos > 0:
        new_method = '''    def map_to_mitre_enhanced(self, message: str) -> List[Dict[str, Any]]:
        """
        Map log message to MITRE ATT&CK techniques with confidence scores.

        Args:
            message: Log message

        Returns:
            List of MITRE techniques with confidence scores
        """
        logger.info(f"[Tool] Enhanced MITRE mapping: {message[:100]}")

        try:
            return self.mapper.map_message_with_confidence(message)
        except Exception as e:
            logger.error(f"Error in map_to_mitre_enhanced: {e}")
            return []

    def get_technique_description(self, technique_id: str) -> str:
        """
        Get detailed description for a MITRE technique.

        Args:
            technique_id: MITRE technique ID

        Returns:
            Technique description
        """
        logger.info(f"[Tool] Getting technique description: {technique_id}")

        try:
            return self.mapper.get_technique_description(technique_id)
        except Exception as e:
            logger.error(f"Error in get_technique_description: {e}")
            return f"MITRE ATT&CK technique {technique_id}"

    '''
        content = content[:insert_pos] + new_method + content[insert_pos:]
        print("[OK] Added enhanced MITRE methods")

# Write back
with open('agents/tools.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Updated tools.py with enhanced MITRE mapper")
