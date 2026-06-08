import re
import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# متغیرهای حساس از سکرت‌های گیت‌هاب
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("TG_SESSION_STRING")

# لیست کانال‌ها و گروه‌های هدف (بدون @)
TARGET_CHANNELS = [
    'channel_username_1',
    'channel_username_2'
]

DECRYPTOR_BOT = '@DickiriptorBot'
BUTTON_TEXT_TARGET = "لینک ویتوریش رو بده" # متنی که روی دکمه شیشه‌ای نوشته شده

V2RAY_REGEX = r'(vless|vmess|trojan|ss|ssr)://[^\s]+'
OUTPUT_FILE = "sub_link.txt"

# پسوند فایل‌های درخواستی شما برای ارسال به ربات رمزگشا
CUSTOM_EXTENSIONS = ('.ehi', '.npv', '.npvt', '.ovpn', '.nm', '.slp', '.tnl', '.rk', '.happ')

async def main():
    extracted_configs = set()

    # بارگذاری کانفیگ‌های قبلی
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    extracted_configs.add(line.strip())

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()

    for target in TARGET_CHANNELS:
        try:
            print(f"Scanning target: {target}")
            async for message in client.iter_messages(target, limit=50):
                
                # ۱. استخراج لینک‌های مستقیم از متن
                if message.text:
                    v2ray_matches = re.findall(V2RAY_REGEX, message.text, re.IGNORECASE)
                    for match in v2ray_matches:
                        extracted_configs.add(match.strip())

                # ۲. پردازش فایل‌های پیوست شده
                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    
                    # الف) پردازش فایل متنی txt
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
                    
                    # ب) فرستادن فرمت‌های خاص به ربات و کلیک روی دکمه شیشه‌ای
                    elif file_name.endswith(CUSTOM_EXTENSIONS):
                        print(f"Found custom config: {file_name}. Forwarding to decryptor...")
                        try:
                            # فوروارد فایل به ربات مبدل
                            await message.forward_to(DECRYPTOR_BOT)
                            await asyncio.sleep(4) # انتظار برای دریافت دکمه‌ها
                            
                            # دریافت آخرین پیام حاوی دکمه‌های شیشه‌ای از ربات
                            async for bot_msg in client.iter_messages(DECRYPTOR_BOT, limit=1):
                                if bot_msg.buttons:
                                    button_clicked = False
                                    
                                    # جستجو در میان دکمه‌های شیشه‌ای پیام
                                    for row in bot_msg.buttons:
                                        for button in row:
                                            # بررسی شباهت متن دکمه (حتی جزیی)
                                            if BUTTON_TEXT_TARGET in button.text or "لینک ویتوری" in button.text:
                                                print(f"Clicking inline button: '{button.text}'")
                                                await button.click()
                                                button_clicked = True
                                                break
                                        if button_clicked:
                                            break
                                    
                                    if button_clicked:
                                        await asyncio.sleep(4) # انتظار برای ارسال لینک بعد از کلیک
                                        
                                        # خواندن پیام جدیدی که حاوی لینک v2ray است
                                        async for link_msg in client.iter_messages(DECRYPTOR_BOT, limit=1):
                                            if link_msg.text:
                                                bot_v2ray = re.findall(V2RAY_REGEX, link_msg.text, re.IGNORECASE)
                                                for match in bot_v2ray:
                                                    print(f"Extracted from button response: {match[:30]}...")
                                                    extracted_configs.add(match.strip())
                        except Exception as bot_err:
                            print(f"Error during button interaction: {bot_err}")

        except Exception as e:
            print(f"Error accessing {target}: {e}")

    # ذخیره نهایی
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for config in sorted(extracted_configs):
            f.write(config + "\n")

    await client.disconnect()
    print("Scraping workflow finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
