import requests
from bs4 import BeautifulSoup
import json
import os
import re

BASE_URL = "https://rusthelp.com"
ITEMS_URL = f"{BASE_URL}/browse/items"
OUTPUT_DIR = "data"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_details(text_block):
    """Extract item details from text block"""
    return {
        "short_name": re.search(r"Short name\s+([^\s]+)", text_block).group(1) if re.search(r"Short name\s+([^\s]+)", text_block) else "N/A",
        "id": re.search(r"ID\s+([^\s]+)", text_block).group(1) if re.search(r"ID\s+([^\s]+)", text_block) else "N/A",
        "stack_size": re.search(r"Stack size\s+(×?\d+)", text_block).group(1) if re.search(r"Stack size\s+(×?\d+)", text_block) else "N/A",
        "despawn_time": re.search(r"Despawn\s+([^\s]+)", text_block).group(1) if re.search(r"Despawn\s+([^\s]+)", text_block) else "N/A"
    }

def scrape_item_page(url):
    """Scrape individual item page for details"""
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_=lambda x: x and 'flex' in x and 'gap-2' in x and 'p-2' in x and 'w-full' in x)
        return extract_details(container.get_text(separator=' ', strip=True)) if container else None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def get_item_links():
    """Get all item links from the browse page"""
    try:
        response = requests.get(ITEMS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        for link in soup.select('a[class*="flex flex-row items-center gap-4"]'):
            img_tag = link.find('img')
            if img_tag:
                # Ensure image URL is absolute
                img_src = img_tag['src']
                if not img_src.startswith(('http://', 'https://')):
                    img_src = f"{BASE_URL}{img_src}" if img_src.startswith('/') else f"{BASE_URL}/{img_src}"
                
                items.append({
                    "name": link.get_text(strip=True),
                    "url": f"{BASE_URL}{link['href']}",
                    "image": img_src,
                    "slug": link['href'].split('/')[-1]
                })
        return items
    except Exception as e:
        print(f"Error getting item links: {e}")
        return []

def generate_markdown(items):
    """Generate comprehensive markdown content"""
    md_content = "# RustHelp Items Collection\n\n"
    md_content += "> Automatically generated from [RustHelp.com](https://rusthelp.com)\n\n"
    md_content += "## Items List\n\n"
    
    # Table of Contents
    md_content += "### Table of Contents\n"
    for item in items:
        md_content += f"- [{item['name']}](#{item['slug'].lower()})\n"
    md_content += "\n---\n\n"
    
    # Detailed Items
    for item in items:
        md_content += f"## {item['name']} {{#{item['slug'].lower()}}}\n\n"
        
        # Image with proper alt text and centered
        if item.get('image'):
            md_content += f"<div align=\"center\">\n\n![{item['name']}]({item['image']} \"{item['name']}\")\n\n</div>\n\n"
        
        # Details table
        md_content += "| Attribute | Value |\n"
        md_content += "|-----------|-------|\n"
        md_content += f"| **Short Name** | `{item.get('short_name', 'N/A')}` |\n"
        md_content += f"| **ID** | `{item.get('id', 'N/A')}` |\n"
        md_content += f"| **Stack Size** | {item.get('stack_size', 'N/A')} |\n"
        md_content += f"| **Despawn Time** | {item.get('despawn_time', 'N/A')} |\n\n"
        
        # Source link
        md_content += f"[🔗 Original Page]({item['url']})\n\n"
        md_content += "---\n\n"
    
    return md_content

def main():
    print("Fetching items from RustHelp...")
    ensure_dir(OUTPUT_DIR)
    items = get_item_links()
    
    if not items:
        print("No items found.")
        return

    print(f"Found {len(items)} items. Processing details...")
    all_items_data = []
    name_to_info = {}

    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] Processing: {item['name']}")
        details = scrape_item_page(item['url'])
        if details:
            full_item = {**item, **details}
            all_items_data.append(full_item)
            name_to_info[full_item['slug']] = {
                "name": full_item['name'],
                "short_name": full_item['short_name'],
                "id": full_item['id']
            }

    # Generate outputs
    print("\nGenerating output files...")
    with open(os.path.join(OUTPUT_DIR, 'items.json'), 'w') as f:
        json.dump(all_items_data, f, indent=2, ensure_ascii=False)

    with open(os.path.join(OUTPUT_DIR, 'name_to_info.json'), 'w') as f:
        json.dump(name_to_info, f, indent=2, ensure_ascii=False)

    md_content = generate_markdown(all_items_data)
    with open(os.path.join(OUTPUT_DIR, 'items.md'), 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"\nDone! Saved {len(all_items_data)} items to '{OUTPUT_DIR}'")
    print(f"- items.json: Full item data")
    print(f"- items.md: Formatted markdown documentation")
    print(f"- name_to_info.json: Mapping of slugs to basic info")

if __name__ == "__main__":
    main()