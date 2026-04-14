import os
import glob
import re

count = 0
for filepath in glob.glob('articles/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The block starts with <div class="flex items-center justify-center gap-4 text-sm font-bold"
    # and ends right before "<!-- SHARE BUTTONS -->"
    
    pattern = r'(<div class="flex items-center justify-center gap-4 text-sm font-bold" style="color: #64748B;">\s*<a href="([^"]+)"[^>]*>([^<]+)</a>\s*<span>&bull;</span>\s*(<time datetime="[^"]+">[^<]+</time>\s*<span[^>]*>&bull;</span>\s*<span[^>]*>[^<]+</span>)\s*</div>)'
    
    def replacer(match):
        author_url = match.group(2)
        author_display = match.group(3)
        time_and_cat = match.group(4)
        
        return f'''<div class="flex flex-wrap items-center justify-center gap-3 text-sm font-bold mt-4" style="color: #64748B;">
                    <a href="{author_url}" class="hover:text-brand transition flex items-center gap-1.5" style="color: inherit; text-decoration: none;">
                        <svg class="w-4 h-4 text-[#F48C06]" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
                        {author_display}
                    </a>
                    <span class="hidden sm:inline">&bull;</span>
                    <span class="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md text-xs border border-emerald-200 shadow-sm" title="Verified Educational Resource | Fact Checked">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                        Fact-Checked Education
                    </span>
                    <span class="hidden sm:inline">&bull;</span>
                    {time_and_cat}
                </div>'''

    new_content, num_subs = re.subn(pattern, replacer, content)
    if num_subs > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        count += 1

print(f"Updated {count} articles with EEAT badges.")
