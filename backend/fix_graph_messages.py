"""Fix agent status messages in graph.py"""
import re

# Read the file
with open('agents/graph.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the code
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # Check if we're at the step_map definition
    if 'step_map = {' in line and i > 0:
        # Keep everything up to and including step_map
        output_lines.append(line)
        # Continue until we find the closing }
        i += 1
        while i < len(lines) and '}' not in lines[i]:
            output_lines.append(lines[i])
            i += 1
        if i < len(lines):
            output_lines.append(lines[i])  # Add the closing }
            i += 1

        # Now add the message_map
        output_lines.append('\n')
        output_lines.append('                    # Detailed status messages showing what each agent does\n')
        output_lines.append('                    message_map = {\n')
        output_lines.append("                        'log_analyst': 'Loading semantic search model and searching log entries',\n")
        output_lines.append("                        'anomaly_hunter': 'Running ML-based anomaly detection (Isolation Forest)',\n")
        output_lines.append("                        'threat_mapper': 'Correlating patterns with MITRE ATT&CK framework',\n")
        output_lines.append("                        'synthesize': 'Combining findings from all consulted agents'\n")
        output_lines.append('                    }\n')

        # Skip lines until we get past any existing message_map or step_name line
        while i < len(lines) and ('step_name = ' not in lines[i]):
            if 'message_map' not in lines[i]:
                output_lines.append(lines[i])
            i += 1

        # Add the step_name and message lines
        output_lines.append('\n')
        output_lines.append('                    step_name = step_map.get(current_agent, current_agent)\n')
        output_lines.append('                    message = message_map.get(current_agent, f\'{current_agent.replace("_", " ").title()} analyzing logs\')\n')

        # Skip the old step_name and message lines
        while i < len(lines) and 'yield {' not in lines[i]:
            i += 1

        # Now handle the yield block - change the message line
        while i < len(lines):
            line = lines[i]
            # Replace the old hardcoded message with the variable
            if "'message':" in line and 'analyzing logs' in line:
                output_lines.append("                        'message': message\n")
                i += 1
                break
            else:
                output_lines.append(line)
                i += 1
                if '}' in line:
                    break
    else:
        output_lines.append(line)
        i += 1

# Write back
with open('agents/graph.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("[OK] Fixed agent status messages in graph.py")
