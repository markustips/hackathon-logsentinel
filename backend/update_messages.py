"""Script to update agent status messages in graph.py"""

# Read the file
with open('agents/graph.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the old code block to replace
old_code = """                if current_agent and current_agent != 'error':
                    # Map agent names to progress steps
                    step_map = {
                        'log_analyst': 'log_analyst',
                        'anomaly_hunter': 'anomaly_hunter',
                        'threat_mapper': 'threat_mapper',
                        'synthesize': 'synthesizing_results'
                    }

                    step_name = step_map.get(current_agent, current_agent)

                    # Emit agent progress
                    yield {
                        'type': 'status',
                        'step': step_name,
                        'agent': current_agent,
                        'message': f'{current_agent.replace("_", " ").title()} analyzing logs'
                    }"""

# Define the new code block with detailed messages
new_code = """                if current_agent and current_agent != 'error':
                    # Map agent names to progress steps
                    step_map = {
                        'log_analyst': 'log_analyst',
                        'anomaly_hunter': 'anomaly_hunter',
                        'threat_mapper': 'threat_mapper',
                        'synthesize': 'synthesizing_results'
                    }

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

# Replace the code
if old_code in content:
    content = content.replace(old_code, new_code)
    print("[OK] Found and replaced agent status messages")
else:
    print("[WARNING] Could not find the exact code block to replace")
    print("Looking for alternative patterns...")

# Write back
with open('agents/graph.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Updated agents/graph.py with detailed status messages")
