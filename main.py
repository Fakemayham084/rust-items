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
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_details(text_block):
    return {
        "short_name": re.search(r"Short name\s+([^\s]+)", text_block).group(1) if re.search(r"Short name\s+([^\s]+)", text_block) else "N/A",
        "id": re.search(r"ID\s+([^\s]+)", text_block).group(1) if re.search(r"ID\s+([^\s]+)", text_block) else "N/A",
        "stack_size": re.search(r"Stack size\s+(×?\d+)", text_block).group(1) if re.search(r"Stack size\s+(×?\d+)", text_block) else "N/A",
        "despawn_time": re.search(r"Despawn\s+([^\s]+)", text_block).group(1) if re.search(r"Despawn\s+([^\s]+)", text_block) else "N/A"
    }

def scrape_item_page(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_=lambda x: x and 'flex' in x and 'gap-2' in x and 'p-2' in x and 'w-full' in x)
        return extract_details(container.get_text(separator=' ', strip=True)) if container else None
    except:
        return None

def get_item_links():
    try:
        response = requests.get(ITEMS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        return [{
            "name": link.get_text(strip=True),
            "url": f"{BASE_URL}{link['href']}",
            "image": link.find('img')['src'] if link.find('img') else None,
            "slug": link['href'].split('/')[-1]
        } for link in soup.select('a[class*="flex flex-row items-center gap-4"]')]
    except:
        return []

def main():
    print("Fetching items...")
    ensure_dir(OUTPUT_DIR)
    items = get_item_links()
    if not items:
        print("No items found.")
        return

    all_items_data = []
    name_to_info = {}
    md_content = "# RustHelp Items Collection\n\n"

    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {item['name']}")
        details = scrape_item_page(item['url'])
        if details:
            full_item = {**item, **details}
            all_items_data.append(full_item)
            name_to_info[full_item['slug']] = {
                "name": full_item['name'],
                "short_name": full_item['short_name'],
                "id": full_item['id']
            }
            md_content += f"## {full_item['name']}\n\n![Image]({full_item['image']})\n\n"
            md_content += f"- **Short Name**: `{full_item['short_name']}`\n"
            md_content += f"- **ID**: `{full_item['id']}`\n"
            md_content += f"- **Stack Size**: {full_item['stack_size']}\n"
            md_content += f"- **Despawn Time**: {full_item['despawn_time']}\n"
            md_content += f"- [View Item]({full_item['url']})\n\n"

    with open(os.path.join(OUTPUT_DIR, 'item.json'), 'w') as f:
        json.dump(all_items_data, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, 'item.md'), 'w') as f:
        f.write(md_content)
    with open(os.path.join(OUTPUT_DIR, 'name_to_info.json'), 'w') as f:
        json.dump(name_to_info, f, indent=2)

    print(f"\nDone! Saved {len(all_items_data)} items to '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()
