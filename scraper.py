import os
import re
import requests
from bs4 import BeautifulSoup

# --- لیست کانال‌های عمومی تلگرام برای جمع‌آوری کانفیگ (بدون @) ---
SOURCE_CHANNELS = [
    'channel_username1', 
    'channel_username2',
    'channel_username3'
]

OUTPUT_FILE = "sub.txt"

# رگرسی قدرتمند برای پیدا کردن پروتکل‌های vless, vmess, trojan
V2RAY_PATTERN = re.compile(r'(vless|vmess|trojan)://[^\s]+')
unique_configs = set()

# ۱. خواندن کانفیگ‌های قبلی از فایل (برای جلوگیری از اضافه شدن تکراری‌ها در هر ساعت)
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                # حذف بخش نام کانفیگ بعد از هشتگ برای مقایسه دقیق هسته اصلی
                base = line.strip().split('#')[0]
                unique_configs.add(base)

def extract_configs_from_text(text):
    """استخراج کانفیگ‌ها و حذف موارد تکراری"""
    found = []
    for match in V2RAY_PATTERN.finditer(text):
        config = match.group(0).strip()
        # پاکسازی تگ‌های HTML احتمالی چسبیده به کانفیگ
        config = config.replace('<br>', '').replace('</div>', '').replace('"', '').replace("'", "")
        
        base_config = config.split('#')[0]
        if base_config not in unique_configs:
            unique_configs.add(base_config)
            found.append(config)
    return found

def scrape_telegram_web(channel_username):
    """خواندن پیام‌های کانال از طریق نسخه وب تلگرام بدون نیاز به اکانت"""
    print(f"[+] Scraping: {channel_username} ...")
    url = f"https://t.me/s/{channel_username}"
    
    # فرستادن هدر مرورگر واقعی تا تلگرام درخواست را مسدود نکند
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[-] Cannot fetch {channel_username}: Status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # پیدا کردن باکس متن پیام‌ها در ساختار وب تلگرام
        message_elements = soup.find_all(class_="tgme_widget_message_text")
        
        channel_configs = []
        for element in message_elements:
            # استخراج متن داخل پیام
            text = element.get_text(separator="\n")
            configs = extract_configs_from_text(text)
            channel_configs.extend(configs)
            
        return channel_configs
    except Exception as e:
        print(f"[-] Error parsing {channel_username}: {e}")
        return []

def main():
    new_configs_count = 0
    
    # باز کردن فایل در حالت Append (اضافه کردن به انتهای فایل)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for channel in SOURCE_CHANNELS:
            configs = scrape_telegram_web(channel)
            for cfg in configs:
                f.write(cfg + "\n")
                new_configs_count += 1
                
    print(f"\n[v] Process Done! Added {new_configs_count} new unique configs.")

if __name__ == "__main__":
    main()
