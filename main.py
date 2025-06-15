import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
import random

BASE_URL = "https://rusthelp.com"
ITEMS_URL = f"{BASE_URL}/browse/items"
OUTPUT_DIR = "data"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
MIN_DELAY = 3  # Minimum delay between requests (seconds)
MAX_DELAY = 8  # Maximum delay between requests (seconds)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def random_delay():
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    print(f"Waiting {delay:.1f} seconds...")
    time.sleep(delay)

def extract_details(text_block):
    details = {
        "short_name": re.search(r"Short name\s+([^\s]+)", text_block).group(1) if re.search(r"Short name\s+([^\s]+)", text_block) else "N/A",
        "id": re.search(r"ID\s+([^\s]+)", text_block).group(1) if re.search(r"ID\s+([^\s]+)", text_block) else "N/A",
        "stack_size": re.search(r"Stack size\s+(×?\d+)", text_block).group(1) if re.search(r"Stack size\s+(×?\d+)", text_block) else "N/A",
        "despawn_time": re.search(r"Despawn\s+([^\s]+)", text_block).group(1) if re.search(r"Despawn\s+([^\s]+)", text_block) else "N/A"
    }
    print(f"Extracted details: {details}")
    return details

def scrape_item_page(url):
    try:
        print(f"\nScraping: {url}")
        random_delay()
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        details_container = soup.find('div', class_=lambda x: x and 'flex' in x and 'gap-2' in x and 'p-2' in x and 'w-full' in x)
        
        if not details_container:
            print("⚠️ Could not find details container")
            return None
            
        return extract_details(details_container.get_text(separator=' ', strip=True))
    except Exception as e:
        print(f"❌ Error scraping page: {str(e)}")
        return None

def get_item_links():
    try:
        print("🔍 Fetching item list from RustHelp...")
        response = requests.get(ITEMS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = [{
            "name": link.get_text(strip=True),
            "url": f"{BASE_URL}{link['href']}",
            "image": link.find('img')['src'] if link.find('img') else None,
            "slug": link['href'].split('/')[-1]
        } for link in soup.select('a[class*="flex flex-row items-center gap-4"]')]
        print(f"✅ Found {len(items)} items to process")
        return items
    except Exception as e:
        print(f"❌ Failed to get item list: {str(e)}")
        return []

def main():
    print("\n" + "="*50)
    print("🚀 Starting RustHelp Item Scraper")
    print(f"⏳ Delays: {MIN_DELAY}-{MAX_DELAY} seconds between requests")
    print("="*50 + "\n")
    
    ensure_dir(OUTPUT_DIR)
    items = get_item_links()
    
    if not items:
        print("❌ No items found, exiting...")
        return
    
    all_items_data = []
    name_to_info = {}
    md_content = "# RustHelp Items Collection\n\n"
    success_count = 0
    
    for i, item in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}] Processing: {item['name']}")
        if details := scrape_item_page(item['url']):
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
            success_count += 1
            print(f"✅ Successfully processed {item['name']}")
        else:
            print(f"⚠️ Skipped {item['name']} due to errors")
    
    print("\n" + "="*50)
    print("💾 Saving results...")
    with open(os.path.join(OUTPUT_DIR, 'item.json'), 'w') as f:
        json.dump(all_items_data, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, 'item.md'), 'w') as f:
        f.write(md_content)
    with open(os.path.join(OUTPUT_DIR, 'name_to_info.json'), 'w') as f:
        json.dump(name_to_info, f, indent=2)
    
    print("\n" + "="*50)
    print(f"🎉 Done! Processed {success_count}/{len(items)} items successfully")
    print(f"📁 Output saved to: {os.path.abspath(OUTPUT_DIR)}")
    print("="*50)

if __name__ == "__main__":
    main()