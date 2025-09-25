import re

def reorder_resource_properties(content: str) -> str:
    """
    Reorders properties in Terraform resource blocks.
    """
    # --- CHANGE HIGHLIGHT: Replaced with manager's full array, split into hierarchical orders for top-level and nested to avoid errors and handle skipping absent keys correctly ---
    top_order = ["log_analytics_workspace_id", "alert_rule_template_guid", "alert_rule_template_version", "name", "display_name", "description", "severity", "tactics", "techniques", "enabled", "entity_mapping", "sentinel_entity_mapping", "custom_details", "alert_details_override", "query_frequency", "query_period", "trigger_operator", "trigger_threshold", "event_grouping", "suppression_enabled", "suppression_duration", "incident_configuration", "query"]
    nested_orders = {
        "incident_configuration": ["create_incident", "grouping"],
        "grouping": ["enabled", "lookback_duration", "entity_matching_method", "group_by_entities", "reopen_closed_incidents"]
    }
    # --- END CHANGE HIGHLIGHT ---

    lines = content.splitlines()
    output = []
    inside_resource = False
    resource_lines = []
    brace_count = 0
    for line in lines:
        stripped = line.strip()
        # Detect start of resource block
        if re.match(r'resource\s+".*"\s+".*"\s*{', stripped):
            inside_resource = True
            resource_lines = [line]
            brace_count = line.count("{") - line.count("}")
            continue
        if inside_resource:
            resource_lines.append(line)
            brace_count += line.count("{") - line.count("}")
           
            # End of resource block
            if brace_count == 0:
                # --- CHANGE HIGHLIGHT: Call the new recursive reorder_block to handle nested structures and prevent repetition at the end ---
                reordered_lines = reorder_block(resource_lines, top_order, nested_orders)
                # --- END CHANGE HIGHLIGHT ---
                output.extend(reordered_lines)
                inside_resource = False
            continue
        # Outside resource, just append
        output.append(line)
    return "\n".join(output)

# --- CHANGE HIGHLIGHT: Added recursive helper function to reorder blocks (top-level and nested), preventing repetition by properly capturing and reconstructing nested content ---
def reorder_block(block_lines: list, order: list, nested_orders: dict) -> list:
    reordered_lines = []
    other_lines = []
    i = 0  # Process from start, as sub-blocks lack declaration
    while i < len(block_lines):
        l = block_lines[i]
        prop_match = re.match(r'\s*(\w+)\s*=', l)
        block_match = re.match(r'\s*(\w+)\s*{\s*', l)
        if block_match:
            prop_name = block_match.group(1)
            sub_block_lines = [l]
            i += 1
            sub_brace_count = 1
            while i < len(block_lines) and sub_brace_count > 0:
                current = block_lines[i]
                sub_block_lines.append(current)
                sub_brace_count += current.count('{') - current.count('}')
                i += 1
            # Recurse on sub-block content
            sub_order = nested_orders.get(prop_name, [])
            formatted_sub = reorder_block(sub_block_lines[1:-1], sub_order, nested_orders)  # Exclude { and }
            sub_block = [sub_block_lines[0]] + formatted_sub + [sub_block_lines[-1]]
            if prop_name in order:
                reordered_lines.append((order.index(prop_name), sub_block))
            else:
                other_lines.append(sub_block)
            continue
        if prop_match:
            prop_name = prop_match.group(1)
            block_lines_prop = [l]
            i += 1
            if "<<-" in l or "<<" in l:
                delimiter = re.search(r'<<-?([A-Z0-9_]+)', l).group(1)
                while i < len(block_lines):
                    block_lines_prop.append(block_lines[i])
                    if block_lines[i].strip() == delimiter:
                        i += 1
                        break
                    i += 1
            if prop_name in order:
                reordered_lines.append((order.index(prop_name), block_lines_prop))
            else:
                other_lines.append(block_lines_prop)
            continue
        other_lines.append([l])
        i += 1

    # Sort and flatten, skipping absent
    reordered_lines.sort(key=lambda x: x[0])
    flat_lines = []
    for _, lines_block in reordered_lines:
        flat_lines.extend(lines_block)
    for lines_block in other_lines:
        flat_lines.extend(lines_block)
    return flat_lines
# --- END CHANGE HIGHLIGHT ---

def align_key_value_pairs(content: str) -> str:
    """
    Aligns the '=' signs for all simple key-value pairs in the content.
    """
    lines = content.splitlines()
    formatted_lines = []
    block = []
    max_key_length = 0
    kv_pattern = re.compile(r'^(\s*)(\w+)\s*=\s+(.*)$')
    for line in lines:
        kv_match = kv_pattern.match(line)
        if kv_match:
            indent, key, value = kv_match.groups()
            if not key.startswith("if") and not key.endswith("=="):
                block.append((indent, key, value))
                max_key_length = max(max_key_length, len(key))
                continue
        if block:
            for indent, key, value in block:
                spaces = ' ' * (max_key_length - len(key))
                formatted_lines.append(f"{indent}{key}{spaces} = {value}")
            block = []
            max_key_length = 0
        formatted_lines.append(line)
    if block:
        for indent, key, value in block:
            spaces = ' ' * (max_key_length - len(key))
            formatted_lines.append(f"{indent}{key}{spaces} = {value}")
    return "\n".join(formatted_lines)
