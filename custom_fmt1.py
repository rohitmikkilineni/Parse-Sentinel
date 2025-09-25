import re

def reorder_resource_properties(content: str) -> str:
    """
    Reorders properties in Terraform resource blocks, including nested blocks recursively.
    """
    # --- CHANGE: Updated preferred order to match manager's full array, split hierarchically for top-level and nested blocks ---
    top_order = ["log_analytics_workspace_id", "alert_rule_template_guid", "alert_rule_template_version", "name", "display_name", "description", "severity", "tactics", "techniques", "enabled", "entity_mapping", "sentinel_entity_mapping", "custom_details", "alert_details_override", "query_frequency", "query_period", "trigger_operator", "trigger_threshold", "event_grouping", "suppression_enabled", "suppression_duration", "incident_configuration", "query"]
    nested_orders = {
        "incident_configuration": ["create_incident", "grouping"],
        "grouping": ["enabled", "lookback_duration", "entity_matching_method", "group_by_entities", "reopen_closed_incidents"]
    }
    # --- END CHANGE ---

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
                # --- CHANGE: Call recursive reorder on the resource lines with top_order ---
                reordered_resource = reorder_block(resource_lines, top_order, nested_orders)
                # --- END CHANGE ---
                output.extend(reordered_resource)
                inside_resource = False
            continue
        # Outside resource, just append
        output.append(line)
    return "\n".join(output)

# --- CHANGE: Added new helper function for recursive reordering of blocks (top-level or nested) ---
def reorder_block(block_lines: list, order: list, nested_orders: dict) -> list:
    reordered_lines = []
    other_lines = []
    i = 0  # Start from 0, as block_lines may be sub-block without declaration
    while i < len(block_lines):
        l = block_lines[i]
        prop_match = re.match(r'\s*(\w+)\s*=', l)
        block_match = re.match(r'\s*(\w+)\s*{\s*', l)  # Detect nested blocks like incident_configuration {
        if block_match:
            prop_name = block_match.group(1)
            # Capture nested block content
            block_content = [l]
            i += 1
            sub_brace_count = 1
            while i < len(block_lines) and sub_brace_count > 0:
                current = block_lines[i]
                block_content.append(current)
                sub_brace_count += current.count('{') - current.count('}')
                i += 1
            # Recurse on nested content with sub-order if available
            sub_order = nested_orders.get(prop_name, order)  # Fallback to main order if no specific
            formatted_sub = reorder_block(block_content[1:-1], sub_order, nested_orders)  # Exclude opening { and closing }
            # Reconstruct nested block
            nested_block = [block_content[0]] + formatted_sub + [block_content[-1]]
            if prop_name in order:
                reordered_lines.append((order.index(prop_name), nested_block))
            else:
                other_lines.append(nested_block)
            continue
        elif prop_match:
            prop_name = prop_match.group(1)
            # Capture multi-line heredoc or simple value
            block_content = [l]
            i += 1
            if '<<' in l:  # Heredoc detection
                delimiter_match = re.search(r'<<-?([A-Z0-9_]+)', l)
                if delimiter_match:
                    delimiter = delimiter_match.group(1)
                    while i < len(block_lines):
                        block_content.append(block_lines[i])
                        if block_lines[i].strip() == delimiter:
                            i += 1
                            break
                        i += 1
            if prop_name in order:
                reordered_lines.append((order.index(prop_name), block_content))
            else:
                other_lines.append(block_content)
            continue
        else:
            other_lines.append([l])
            i += 1

    # Sort reordered and flatten
    reordered_lines.sort(key=lambda x: x[0])
    flat_lines = []
    for _, lines_block in reordered_lines:
        flat_lines.extend(lines_block)
    for lines_block in other_lines:
        flat_lines.extend(lines_block)

    # If this is a top-level resource block, include declaration and closing brace
    if block_lines and re.match(r'resource\s+".*"\s+".*"\s*{', block_lines[0].strip()):
        return [block_lines[0]] + flat_lines + [block_lines[-1]]  # Add back resource { and }
    else:
        return flat_lines
# --- END CHANGE ---

def align_key_value_pairs(content: str) -> str:
    """
    Aligns the '=' signs for all simple key-value pairs in the content.
    """
    lines = content.splitlines()
    formatted_lines = []
    block = []
    max_key_length = 0
    # Match only the first "=" (not "=="), splitting key from value
    kv_pattern = re.compile(r'^(\s*)(\w+)\s*=\s+(.*)$')
    for line in lines:
        kv_match = kv_pattern.match(line)
        if kv_match:
            indent, key, value = kv_match.groups()
            # Exclude lines that *start* with something like "if (...) ==" (heredoc code)
            if not key.startswith("if") and not key.endswith("=="):
                block.append((indent, key, value))
                max_key_length = max(max_key_length, len(key))
                continue
        # Flush current block if exists
        if block:
            for indent, key, value in block:
                spaces = ' ' * (max_key_length - len(key))
                formatted_lines.append(f"{indent}{key}{spaces} = {value}")
            block = []
            max_key_length = 0
        formatted_lines.append(line)
    # Flush any remaining block
    if block:
        for indent, key, value in block:
            spaces = ' ' * (max_key_length - len(key))
            formatted_lines.append(f"{indent}{key}{spaces} = {value}")
    return "\n".join(formatted_lines)
