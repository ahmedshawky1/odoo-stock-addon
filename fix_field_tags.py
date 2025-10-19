#!/usr/bin/env python3
"""
Fix unclosed field tags in XML files
"""

import os
import re

def fix_field_tags(file_path):
    """Fix unclosed field tags in a single XML file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Pattern for field tags that end with ">" but should be self-closing
    # Match: <field name="something">
    # But NOT: <field name="something">...content...</field>
    # Look for field tags followed by whitespace and newline without closing content
    pattern = r'(<field[^>]*?name="[^"]*"[^>]*?)>\s*$'
    
    # Find all matches
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    
    # Process matches in reverse order to avoid offset issues
    for match in reversed(matches):
        line_start = content.rfind('\n', 0, match.start()) + 1
        line_end = content.find('\n', match.end())
        if line_end == -1:
            line_end = len(content)
        
        # Get the full line
        line = content[line_start:line_end]
        
        # Check if this is a field that should be self-closing
        # (no content between opening and closing tag)
        next_tag_pos = content.find('<', match.end())
        if next_tag_pos == -1:
            next_tag_pos = len(content)
            
        # Check if the next tag is a closing field tag
        between_content = content[match.end():next_tag_pos].strip()
        if not between_content:  # No content between tags
            # Replace the ">" with "/>"
            field_tag = match.group(1)
            new_tag = field_tag + "/>"
            content = content[:match.start()] + new_tag + content[match.end():]
            changes_made += 1
            print(f"Fixed field tag: {field_tag}")
    
    # Write back if changes were made
    if changes_made > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed {changes_made} field tags in {file_path}")
    
    return changes_made

def main():
    """Fix field tags in all XML view files"""
    views_dir = "/var/odoo/addons/stock/stock_market_simulation/views"
    
    total_fixes = 0
    for filename in os.listdir(views_dir):
        if filename.endswith('.xml'):
            file_path = os.path.join(views_dir, filename)
            fixes = fix_field_tags(file_path)
            total_fixes += fixes
    
    print(f"\nTotal fixes applied: {total_fixes}")

if __name__ == "__main__":
    main()