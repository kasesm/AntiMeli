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
# تنظیمات و متغیرهای پایه
# ----------------------------------------
# دریافت اطلاعات از متغیرهای محیطی گیت‌هاب (با مقادیر پیش‌فرض امن برای جلوگیری از کرش)
API_ID_ENV = os.getenv("TELEGRAM_API_ID", "")
API_ID = int(API_ID_ENV) if API_ID_ENV.isdigit() else 123456
API_HASH = os.getenv("TELEGRAM_API_HASH", "your_api_hash_here")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "").strip()

# کلیدها و IV رمزگشایی نپسترنت (مقادیر اختصاصی خود را جایگزین کنید)
NPV_KEY = b"1234567890123456"  
NPV_IV = b"1234567890123456"   

NPV_EXTENSIONS = ('.npv', '.npvt')
TXT_EXTENSIONS = ('.txt',)

# ریجکس اصلاح‌شده بدون پرانتز کپچرینگ مزاحم
V2RAY_REGEX = r'(?:vless|vmess|trojan|ss|ssr)://[^\s]+'

# لیست کانال‌های هدف برای اسکن
CHANNELS = [
    "marambashi",
    "v2freehub",
    "capoit",
    "prrofile_purple"
]

# ----------------------------------------
# تابع هوشمند رمزگشایی نپسترنت
# ----------------------------------------
def decrypt_npv_data(encrypted_text):
    """رمزگشایی پیشرفته فایل‌های نپسترنت با اصلاح طول بیس۶۴ و ساپورت Base64Url"""
    try:
        encrypted_text = encrypted_text.strip()
        
        if encrypted_text.startswith('{') and encrypted_text.endswith('}'):
            try:
                js = json.loads(encrypted_text)
                if 'config' in js:
                    encrypted_text = js['config']
                elif 'data' in js:
                    encrypted_text = js['data']
            except Exception:
                pass

        tokens = encrypted_text.split()
        best_token = ""
        max_len = 0
        for t in tokens:
            t = t.replace('-', '+').replace('_', '/')
            cleaned = re.sub(r'[^A-Za-z0-9+/]', '', t)
            if len(cleaned) > max_len:
                max_len = len(cleaned)
                best_token = cleaned

        if max_len < 20: 
            return []

        # جراحی ریاضی طول رشته Base64 (باقی‌مانده ۱ غیرممکن است)
        if len(best_token) % 4 == 1:
            best_token = best_token[:-1]

        missing_padding = len(best_token) % 4
        if missing_padding:
            best_token += '=' * (4 - missing_padding)
            
        try:
            encrypted_bytes = base64.b64decode(best_token)
        except Exception as b64_e:
            print(f"Base64 Decode Failed for token: {b64_e}")
            return []
        
        try:
            plain_str = encrypted_bytes.decode('utf-8', errors='strict')
            if '{' in plain_str or '://' in plain_str:
                return re.findall(V2RAY_REGEX, plain_str, re.IGNORECASE)
        except Exception:
            pass

        if len(encrypted_bytes) % 16 != 0:
            try:
                raw_test = encrypted_bytes.decode('utf-8', errors='ignore')
                return re.findall(V2RAY_REGEX, raw_test, re.IGNORECASE)
            except Exception:
                return []

        try:
            cipher = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            decrypted_str = decrypted_bytes.decode('utf-8', errors='ignore')
            return re.findall(V2RAY_REGEX, decrypted_str, re.IGNORECASE)
        except Exception as aes_err:
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
# تابع اصلی اسکرپر و ارتباط با تلگرام
# ----------------------------------------
async def main():
    extracted_configs = set()
    
    # 🛡️ سیستم بررسی امنیتی سشن برای جلوگیری از کرش مجدد و نمایش خطای شفاف
    if not SESSION_STRING or SESSION_STRING == "your_session_string_here":
        print("\n" + "="*60)
        print("[❌ ERROR] TELEGRAM_SESSION is completely EMPTY or INVALID!")
        print("Please check your GitHub Repository Secrets (Settings -> Secrets -> Actions).")
        print("Ensure TELEGRAM_SESSION contains a valid Telethon String Session.")
        print("="*60 + "\n")
        return

    print("Connecting to Telegram client...")
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.connect()
    except ValueError as init_err:
        print("\n" + "="*60)
        print(f"[❌ TELETHON CRASH] ValueError: {init_err}")
        print("The string session you provided format is NOT recognized by Telethon.")
        print("Make sure you are NOT using a Pyrogram session (which starts with BQ...).")
        print("="*60 + "\n")
        return
    except Exception as e:
        print(f"[❌ UNKNOWN ERROR] Could not initialize client: {e}")
        return
    
    if not await client.is_user_authorized():
        print("[❌ ERROR] Telegram client is not authorized! Check your Session String.")
        return

    print("Authorization successful. Starting scan...")

    for channel in CHANNELS:
        print(f"\nScanning target channel: @{channel}")
        try:
            async for message in client.iter_messages(channel, limit=50):
                
                # لایه اول: اسکن متون عادی
                if message.text:
                    text_links = re.findall(V2RAY_REGEX, message.text, re.IGNORECASE)
                    for link in text_links:
                        extracted_configs.add(link.strip())
                
                # لایه دوم: اسکن فایل‌ها
                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    
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
                            if os.path.exists(path): os.remove(path)
                                
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
                            if os.path.exists(path): os.remove(path)
                                
        except Exception as chan_err:
            print(f"Could not scan channel {channel}: {chan_err}")

    print(f"\nScan finished. Total unique configs found: {len(extracted_configs)}")
    
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
