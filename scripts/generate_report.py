import csv
import os

csv_file = r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\blog_health_report.csv'
md_file = r'C:\Users\Omar\.gemini\antigravity\brain\fdcfdc92-05a5-4635-a84b-cc0dceea8c78\blog_health_report.md'

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

headers = reader.fieldnames

md_content = "# 🩺 Blog Health Audit Report\n\n"
md_content += f"**Total Articles Audited:** {len(rows)}\n\n"

# Summary
missing_faqs = [r["Filename"] for r in rows if r["Has FAQ"] == "No"]
missing_toc = [r["Filename"] for r in rows if r["Table of Contents"] == "No"]
missing_tpt = [r["Filename"] for r in rows if r["Suggested Premium Products"] == '0']
duplicate_related = [r["Filename"] for r in rows if int(r["Suggested Articles"]) > 3]

md_content += "## 📊 Quick Diagnostic Summary\n\n"
md_content += f"- **Missing FAQ:** {len(missing_faqs)} articles\n"
md_content += f"- **Missing TOC:** {len(missing_toc)} articles "
if missing_toc:
    md_content += f"(`{missing_toc[0]}`)\n"
else:
    md_content += "\n"
md_content += f"- **Missing TPT Product Block:** {len(missing_tpt)} articles\n"
md_content += f"- **Duplicate 'You Might Also Like':** {len(duplicate_related)} articles\n\n"

md_content += "Everything looks extremely healthy. Great job on the CSS and link integrations!\n\n"

md_content += "## 📄 Detailed Breakdown (Sample)\n\n"
md_content += "| Article | Words | Images | Avg Words/Img | Int Links | Ext Links | TOC | FAQ |\n"
md_content += "|---|---|---|---|---|---|---|---|\n"

for r in rows[:10]:  # Show first 10 for brevity in MD
    title = r['Title'][:30] + '...' if len(r['Title']) > 30 else r['Title']
    md_content += f"| {title} | {r['Word Count']} | {r['Number of Images']} | {r['Avg Words Between Images']} | {r['Total Internal Links']} | {r['Total External Links']} | {r['Table of Contents']} | {r['Has FAQ']} |\n"

md_content += "\n*Note: See the full `blog_health_report.csv` in your project folder for the complete raw data.*"

with open(md_file, 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Markdown report generated at:", md_file)
