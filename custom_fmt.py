import re

def reorder_resource_properties(content: str) -> str:
    """
    Reorders properties in Terraform resource blocks.
    """
    preferred_order = ["suppression_duration", "query", "display_name", "description", "name", "severity", "tactics"]

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
                # Reorder properties inside the block
                reordered_lines = []
                other_lines = []

                # Collect property blocks
                i = 1  # skip first line (resource declaration)
                while i < len(resource_lines) - 1:  # skip last line (closing brace)
                    l = resource_lines[i]
                    prop_match = re.match(r'\s*(\w+)\s*=', l)
                    if prop_match:
                        prop_name = prop_match.group(1)
                        # Capture multi-line heredoc or block
                        block_lines = [l]
                        i += 1
                        if "<<-" in l or "<<" in l:  # heredoc
                            delimiter = re.search(r'<<-?([A-Z0-9_]+)', l).group(1)
                            while i < len(resource_lines) - 1:
                                block_lines.append(resource_lines[i])
                                if resource_lines[i].strip() == delimiter:
                                    i += 1
                                    break
                                i += 1
                        # Save in order dict
                        if prop_name in preferred_order:
                            reordered_lines.append((preferred_order.index(prop_name), block_lines))
                        else:
                            other_lines.append(block_lines)
                    else:
                        other_lines.append([l])
                        i += 1

                # Sort by preferred order and flatten
                reordered_lines.sort(key=lambda x: x[0])
                flat_lines = []
                for _, lines_block in reordered_lines:
                    flat_lines.extend(lines_block)
                for lines_block in other_lines:
                    flat_lines.extend(lines_block)

                # Append resource declaration and closing brace
                output.append(resource_lines[0])
                output.extend(flat_lines)
                output.append(resource_lines[-1])

                inside_resource = False
            continue

        # Outside resource, just append
        output.append(line)

    return "\n".join(output)

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
