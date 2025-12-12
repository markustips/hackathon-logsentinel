"""Fix indentation error in tools.py"""

# Read file
with open('agents/tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation issue - get_timeline should not be indented under get_technique_description
old_section = """        try:
            return self.mapper.get_technique_description(technique_id)
        except Exception as e:
            logger.error(f"Error in get_technique_description: {e}")
            return f"MITRE ATT&CK technique {technique_id}"

        def get_timeline(self, file_id: str) -> List[Dict[str, Any]]:"""

new_section = """        try:
            return self.mapper.get_technique_description(technique_id)
        except Exception as e:
            logger.error(f"Error in get_technique_description: {e}")
            return f"MITRE ATT&CK technique {technique_id}"

    def get_timeline(self, file_id: str) -> List[Dict[str, Any]]:"""

if old_section in content:
    content = content.replace(old_section, new_section)
    print("[OK] Fixed indentation for get_timeline method")
else:
    print("[ERROR] Could not find exact match")

# Write back
with open('agents/tools.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Fixed agents/tools.py indentation")
