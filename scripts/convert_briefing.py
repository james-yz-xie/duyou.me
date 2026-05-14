#!/usr/bin/env python3
"""
Convert Obsidian Briefing markdown to Astro briefings.astro format
"""
import re
from datetime import datetime

def parse_briefing(md_file):
    """Parse the briefing markdown file and extract structured data"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract date from filename or first line
    date_match = re.search(r'Briefing_(\d{4}-\d{2}-\d{2})', md_file)
    if date_match:
        briefing_date = date_match.group(1)
    else:
        date_match = re.search(r'#.*?(\d{4}-\d{2}-\d{2})', content)
        briefing_date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
    
    # Define sections mapping
    section_mapping = {
        '🏛️ 工业界巨头 (Big Tech)': 'big_tech',
        '📰 顶级媒体 (Top Media)': 'top_media',
        '🎓 学术界前沿 (Academia)': 'academia',
        '🔥 社区与工程 (Community)': 'community'
    }
    
    sections = {}
    current_section = None
    
    # Split by lines and process
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Check for section headers
        for header, section_key in section_mapping.items():
            if header in line:
                current_section = section_key
                sections[current_section] = []
                break
        
        # Parse items in current section
        if current_section and line.strip().startswith('- **['):
            # Parse item line: - **[Source] Title** (Score: X.X) [Date]
            item_match = re.match(r'-\s+\*\*\[(.*?)\]\s+(.*?)\*\*\s+\(Score:\s+([\d.]+)\)\s+\[(\d{4}-\d{2}-\d{2})\]', line)
            if item_match:
                source = item_match.group(1)
                title_en = item_match.group(2)
                score = float(item_match.group(3))
                date = item_match.group(4)
                
                # Get link from next line
                link_line = lines[i + 1] if i + 1 < len(lines) else ''
                link_match = re.search(r'🔗 Link: (.+)', link_line)
                link = link_match.group(1).strip() if link_match else None
                
                # Get summary from line after link
                summary_line = lines[i + 2] if i + 2 < len(lines) else ''
                summary_match = re.search(r'📝 \*(.+?)\*', summary_line)
                summary_en = summary_match.group(1).strip() if summary_match else ''
                
                # Truncate summary if too long
                if len(summary_en) > 200:
                    summary_en = summary_en[:197] + '...'
                
                # Create Chinese title (use English for now, can be translated later)
                title_zh = title_en
                summary_zh = summary_en
                
                item = {
                    'title': {'zh': title_zh, 'en': title_en},
                    'date': date,
                    'summary': {'zh': summary_zh, 'en': summary_en},
                    'links': [{'label': source, 'href': link}] if link else []
                }
                
                sections[current_section].append(item)
    
    return sections, briefing_date

def generate_astro_code(sections, briefing_date):
    """Generate Astro code for briefings.astro"""
    
    section_names = {
        'big_tech': {'zh': '工业界巨头', 'en': 'Big Tech'},
        'top_media': {'zh': '顶级媒体', 'en': 'Top Media'},
        'academia': {'zh': '学术界前沿', 'en': 'Academia'},
        'community': {'zh': '社区与工程', 'en': 'Community'}
    }
    
    icons = {
        'big_tech': '🏛️',
        'top_media': '📰',
        'academia': '🎓',
        'community': '🔥'
    }
    
    output = []
    output.append('---')
    output.append("import Layout from '../layouts/Layout.astro';")
    output.append("import Footer from '../components/Footer.astro';")
    output.append('')
    output.append(f'// Generated from Briefing_{briefing_date}.md')
    output.append(f'const generatedDate = "{briefing_date}";')
    output.append('')
    output.append('const sections = [')
    
    for section_key in ['big_tech', 'top_media', 'academia', 'community']:
        if section_key not in sections or not sections[section_key]:
            continue
        
        section_data = sections[section_key]
        names = section_names[section_key]
        icon = icons[section_key]
        
        output.append('  {')
        output.append(f"    icon: '{icon}',")
        output.append('    title: {')
        output.append(f"      zh: '{names['zh']}',")
        output.append(f"      en: '{names['en']}'")
        output.append('    },')
        output.append('    items: [')
        
        for item in section_data:
            title_zh = item['title']['zh'].replace("'", "\\'")
            title_en = item['title']['en'].replace("'", "\\'")
            summary_zh = item['summary']['zh'].replace("'", "\\'")
            summary_en = item['summary']['en'].replace("'", "\\'")
            
            output.append('      {')
            output.append('        title: {')
            output.append(f"          zh: '{title_zh}',")
            output.append(f"          en: '{title_en}'")
            output.append('        },')
            output.append(f"        date: '{item['date']}',")
            output.append('        summary: {')
            output.append(f"          zh: '{summary_zh}',")
            output.append(f"          en: '{summary_en}'")
            output.append('        },')
            
            if item['links']:
                output.append('        links: [')
                for link in item['links']:
                    label = link['label'].replace("'", "\\'")
                    href = link['href'].replace("'", "\\'")
                    output.append(f"          {{ label: '{label}', href: '{href}' }}")
                output.append('        ]')
            
            output.append('      },')
        
        output.append('    ]')
        output.append('  },')
    
    output.append('];')
    output.append('---')
    
    return '\n'.join(output)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python convert_briefing.py <briefing_md_file>")
        sys.exit(1)
    
    md_file = sys.argv[1]
    sections, date = parse_briefing(md_file)
    
    print(f"Parsed briefing from {date}")
    for section_key, items in sections.items():
        print(f"  {section_key}: {len(items)} items")
    
    astro_code = generate_astro_code(sections, date)
    
    # Write to output file
    output_file = '/tmp/briefings_generated.astro'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(astro_code)
    
    print(f"\nGenerated Astro code saved to: {output_file}")
    print(f"Total sections: {len(sections)}")
