import sys
import re

file_path = r"c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\articles\elementary-spelling-worksheets-ultimate-guide.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

tpt_marker = "<!-- ═══ TPT PRODUCT RECOMMENDATION & SCHEMA ═══ -->"
parts = content.split(tpt_marker)
if len(parts) > 2:
    # We have duplicates.
    # The first part is before the first marker.
    # The second part is the TPT block AND EVERYTHING until the next marker.
    # Wait, if there are multiple contiguous blocks, the parts between them are empty or just whitespace.
    
    # Simple fix: Let's remove ALL instances of the TPT block except the first one.
    # Since we know where the block ends, we can extract the first block, and then remove everything between the first marker and the end of the last duplicate block.
    # Actually, simpler:
    end_marker = "Browse All Products\n                    </a>\n                </div>\n            </div>\n        </div>"
    if end_marker in content:
        start_idx = content.find(tpt_marker)
        if start_idx != -1:
            end_idx = content.find(end_marker, start_idx) + len(end_marker)
            full_block = content[start_idx:end_idx]
            
            # Replace all occurrences with ___TOKEN___
            content = content.replace(full_block, "___TPT___")
            # Remove all contiguous tokens
            content = re.sub(r'(___TPT___\s*)+', '___TPT___\n', content)
            # Put back the block
            content = content.replace("___TPT___", full_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fix applied to elementary-spelling-worksheets-ultimate-guide.html")
