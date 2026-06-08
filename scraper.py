import re
import os
import json
import base64
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ----------------------------------------
# ۱. تنظیمات و متغیرهای پایه
# ----------------------------------------
# اطلاعات تلگرام (بهتر است از Environment Variables خوانده شوند)
API_ID = int(os.getenv("TELEGRAM_API_ID", 123456))  # جایگزین کن یا در اینوایرومنت ست کن
API_HASH = os.getenv("TELEGRAM_API_HASH", "your_api_hash_here")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "your_session_string_here")

# کلیدها و IV اختصاصی رمزگشایی نپسترنت (مقادیر خود را جایگزین کنید)
NPV_KEY = b"1234567890123456"  # کلید ۱۶ بایتی شما
NPV_IV = b"1234567890123456"   # پارامتر IV ۱۶ بایتی شما

# پسوندهای مورد حمایت
NPV_EXTENSIONS = ('.npv', '.npvt')
TXT_EXTENSIONS = ('.txt',)

# ریجکس اصلاح‌شده برای استخراج کامل لینک‌های v2ray (بدون پرانتز کاپچرینگ مزاحم)
V2RAY_REGEX = r'(?:vless|vmess|trojan|ss|ssr)://[^\s]+'

# لیست کانال‌های هدف برای اسکن
CHANNELS = [
    "marambashi",
    "v2freehub",
    "capoit",
    "prrofile_purple"
    # آیدی بقیه کانال‌ها را بدون @ اینجا اضافه کن
]

# ----------------------------------------
# ۲. تابع هوشمند رمزگشایی نپسترنت
# ----------------------------------------
def decrypt_npv_data(encrypted_text):
    """رمزگشایی پیشرفته فایل‌های نپسترنت با اصلاح طول بیس۶۴ و ساپورت Base64Url"""
    try:
        encrypted_text = encrypted_text.strip()
        
        # الف) بررسی ساختار احتمالی JSON کپسوله شده (کلاود کلاینت‌ها)
        if encrypted_text.startswith('{') and encrypted_text.endswith('}'):
            try:
                js = json.loads(encrypted_text)
                if 'config' in js:
                    encrypted_text = js['config']
                elif 'data' in js:
                    encrypted_text = js['data']
            except Exception:
                pass

        # ب) فیلتر کردن توکن اصلی فایل (حذف آیدی چنل‌ها و متن‌های اضافه ادمین‌ها)
        tokens = encrypted_text.split()
        best_token = ""
        max_len = 0
        for t in tokens:
            # تبدیل فرمت احتمالی Base64Url به بیس۶۴ استاندارد
            t = t.replace('-', '+').replace('_', '/')
            cleaned = re.sub(r'[^A-Za-z0-9+/]', '', t)
            if len(cleaned) > max_len:
                max_len = len(cleaned)
                best_token = cleaned

        if max_len < 20: 
            return []

        # ج) جراحی ریاضی طول رشته Base64 (باقی‌مانده ۱ در بیس۶۴ غیرممکن است)
        if len(best_token) % 4 == 1:
            best_token = best_token[:-1]

        # د) پادینگ زدن استاندارد با علامت =
        missing_padding = len(best_token) % 4
        if missing_padding:
            best_token += '=' * (4 - missing_padding)
            
        # هـ) دکود اولیه از Base64 به بایت
        try:
            encrypted_bytes = base64.b64decode(best_token)
        except Exception as b64_e:
            print(f"Base64 Decode Failed for token: {b64_e}")
            return []
        
        # و) تست متن ساده (اگر فایل اصلاً رمزنگاری AES نداشت و فقط بیس۶۴ خالی بود)
        try:
            plain_str = encrypted_bytes.decode('utf-8', errors='strict')
            if '{' in plain_str or '://' in plain_str:
                return re.findall(V2RAY_REGEX, plain_str, re.IGNORECASE)
        except Exception:
            pass

        # ز) بررسی طول بلاک برای الگوریتم AES-16
        if len(encrypted_bytes) % 16 != 0:
            try:
                raw_test = encrypted_bytes.decode('utf-8', errors='ignore')
                return re.findall(V2RAY_REGEX, raw_test, re.IGNORECASE)
            except Exception:
                return []

        # ح) اجرای الگوریتم اصلی دکریپت AES-CBC
        try:
            cipher = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            decrypted_str = decrypted_bytes.decode('utf-8', errors='ignore')
            return re.findall(V2RAY_REGEX, decrypted_str, re.IGNORECASE)
        except Exception as aes_err:
            # ط) لایه نجات‌بخش هک پدینگ (بای‌پاس ارورهای Unpad اندروید)
            print(f"Standard unpad failed ({aes_err}). Trying brute-force extraction...")
            try:
                cipher_bypass = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
                raw_decrypted = cipher_bypass.decrypt(encrypted_bytes).decode('utf-8', errors='ignore')
                return re.findall(V2RAY_REGEX, raw_decrypted, re.IGNORECASE)
            except Exception:
                return []

    except Exception as e:
        print(f"Advanced Decryption Failed: {e}")
        return []

# ----------------------------------------
# ۳. تابع اصلی اسکرپر و ارتباط با تلگرام
# ----------------------------------------
async def main():
    # ساخت ست‌ کلکتور برای ذخیره کانفیگ‌های کاملاً یکتا
    extracted_configs = set()
    
    print("Connecting to Telegram client...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("Error: Telegram client is not authorized! Check your Session String.")
        return

    print("Authorization successful. Starting scan...")

    for channel in CHANNELS:
        print(f"\nScanning target channel: @{channel}")
        try:
            # بررسی ۵۰ پیام اخیر هر کانال
            async for message in client.iter_messages(channel, limit=50):
                
                # لایه اول: اسکن متون عادی داخل پیام‌ها
                if message.text:
                    text_links = re.findall(V2RAY_REGEX, message.text, re.IGNORECASE)
                    for link in text_links:
                        extracted_configs.add(link.strip())
                
                # لایه دوم: اسکن فایل‌های پیوستی (نپسترنت و تکست)
                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    
                    # بررسی فایل‌های نپسترنت (.npv یا .npvt)
                    if file_name.endswith(NPV_EXTENSIONS):
                        print(f"Found NapsternetV file: {message.file.name}. Processing locally...")
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                npv_content = f.read()
                                local_links = decrypt_npv_data(npv_content)
                                for link in local_links:
                                    extracted_configs.add(link.strip())
                        except Exception as file_err:
                            print(f"Error reading NPV file {file_name}: {file_err}")
                        finally:
                            if os.path.exists(path): 
                                os.remove(path)
                                
                    # بررسی فایل‌های متنی ساده (.txt)
                    elif file_name.endswith(TXT_EXTENSIONS):
                        print(f"Found Text file: {message.file.name}. Extracting links...")
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                txt_content = f.read()
                                txt_links = re.findall(V2RAY_REGEX, txt_content, re.IGNORECASE)
                                for link in txt_links:
                                    extracted_configs.add(link.strip())
                        except Exception as file_err:
                            print(f"Error reading TXT file {file_name}: {file_err}")
                        finally:
                            if os.path.exists(path): 
                                os.remove(path)
                                
        except Exception as chan_err:
            print(f"Could not scan channel {channel}: {chan_err}")

    # ----------------------------------------
    # ۴. ذخیره‌سازی خروجی نهایی
    # ----------------------------------------
    print(f"\nScan finished. Total unique configs found: {len(extracted_configs)}")
    
    # ذخیره در فایل خروجی (مثلاً برای سابلینک پروژه Alireza's Collector)
    output_file = "configs.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as out:
            for config in sorted(extracted_configs):
                out.write(config + "\n")
        print(f"Successfully saved all configs to {output_file}")
    except Exception as save_err:
        print(f"Failed to save configs to file: {save_err}")

if __name__ == "__main__":
    asyncio.run(main())
