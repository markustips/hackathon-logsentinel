"""Final fix for agent status messages"""

# Read file
with open('agents/graph.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Add message_map after step_map
old_section = """                    }

                    step_name = step_map.get(current_agent, current_agent)
                    message = message_map.get(current_agent, f'{current_agent.replace("_", " ").title()} analyzing logs')

                    # Emit agent progress
                    yield {
                        'type': 'status',
                        'step': step_name,
                        'agent': current_agent,
                        'message': f'{current_agent.replace("_", " ").title()} analyzing logs'
                    }"""

new_section = """                    }

                    # Detailed status messages showing what each agent does
                    message_map = {
                        'log_analyst': 'Loading semantic search model and searching log entries',
                        'anomaly_hunter': 'Running ML-based anomaly detection (Isolation Forest)',
                        'threat_mapper': 'Correlating patterns with MITRE ATT&CK framework',
                        'synthesize': 'Combining findings from all consulted agents'
                    }

                    step_name = step_map.get(current_agent, current_agent)
                    message = message_map.get(current_agent, f'{current_agent.replace("_", " ").title()} analyzing logs')

                    # Emit agent progress with detailed status
                    yield {
                        'type': 'status',
                        'step': step_name,
                        'agent': current_agent,
                        'message': message
                    }"""

if old_section in content:
    content = content.replace(old_section, new_section)
    print("[OK] Fixed agent status messages")
else:
    print("[ERROR] Could not find exact match")

# Also update the initial orchestrator message
content = content.replace(
    "'message': 'Analyzing query and routing to specialist agents'",
    "'message': 'Analyzing query intent and routing to specialist agents'"
)

# Write back
with open('agents/graph.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Updated agents/graph.py")
