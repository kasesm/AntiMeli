import re
import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# دریافت اطلاعات حساس از سکرت‌های گیت‌هاب
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("TG_SESSION_STRING")

# آیدی کانال‌ها و گروه‌های منبع (بدون @ وارد کن)
TARGET_CHANNELS = [
    'channel_username_1',
    'channel_username_2'
]

# ربات رمزگشا برای فرمت‌های خاص
DECRYPTOR_BOT = '@DickiriptorBot'

# الگوی شناسایی لینک‌های استاندارد V2Ray
V2RAY_REGEX = r'(vless|vmess|trojan|ss|ssr)://[^\s]+'
OUTPUT_FILE = "sub_link.txt"

async def main():
    extracted_configs = set()

    # بارگذاری کانفیگ‌های قبلی برای جلوگیری از حذف شدن آنها
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    extracted_configs.add(line.strip())

    # اتصال به تلگرام از طریق سشن گیت‌هاب
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()

    for target in TARGET_CHANNELS:
        try:
            print(f"Scanning target: {target}")
            # بررسی ۵۰ پیام اخیر برای سرعت بیشتر در اجرای یک ساعته
            async for message in client.iter_messages(target, limit=50):
                
                # ۱. استخراج لینک‌های مستقیم از متن پیام
                if message.text:
                    v2ray_matches = re.findall(V2RAY_REGEX, message.text, re.IGNORECASE)
                    for match in v2ray_matches:
                        extracted_configs.add(match.strip())

                # ۲. بررسی فایل‌های پیوست شده
                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    
                    # الف) اگر فایل متنی txt بود، داخلش را اسکن کن
                    if file_name.endswith('.txt'):
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                file_content = f.read()
                                file_v2ray = re.findall(V2RAY_REGEX, file_content, re.IGNORECASE)
                                for match in file_v2ray:
                                    extracted_configs.add(match.strip())
                        except Exception as e:
                            print(f"Error reading txt file: {e}")
                        finally:
                            if os.path.exists(path):
                                os.remove(path)
                    
                    # ب) اگر فایل از فرمت‌های خاص بود، آن را به ربات دیکریپتور بفرست
                    elif file_name.endswith(('.ehi', '.npv', '.npvt', '.ovpn')):
                        print(f"Found custom config file: {file_name}. Forwarding to decryptor...")
                        try:
                            # فوروارد فایل به ربات مبدل
                            await message.forward_to(DECRYPTOR_BOT)
                            # ۵ ثانیه صبر می‌کنیم تا ربات پاسخ را پردازش و ارسال کند
                            await asyncio.sleep(5)
                            
                            # خواندن آخرین پیام دریافتی از ربات مبدل
                            async for bot_msg in client.iter_messages(DECRYPTOR_BOT, limit=1):
                                if bot_msg.text:
                                    bot_v2ray = re.findall(V2RAY_REGEX, bot_msg.text, re.IGNORECASE)
                                    for match in bot_v2ray:
                                        print(f"Successfully converted via bot: {match[:30]}...")
                                        extracted_configs.add(match.strip())
                        except Exception as bot_err:
                            print(f"Error converting via decryptor bot: {bot_err}")

        except Exception as e:
            print(f"Error accessing {target}: {e}")

    # ذخیره نهایی تمام کانفیگ‌های یکتا و تمیز در فایل سابلینک
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for config in sorted(extracted_configs):
            f.write(config + "\n")

    await client.disconnect()
    print("Scraping workflow finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
