import re
import os
import json
import base64
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityTextUrl, ReplyInlineMarkup, KeyboardButtonUrl
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ----------------------------------------
# تنظیمات و متغیرهای پایه
# ----------------------------------------
API_ID_ENV = os.getenv("TELEGRAM_API_ID", "")
API_ID = int(API_ID_ENV) if API_ID_ENV.isdigit() else 123456
API_HASH = os.getenv("TELEGRAM_API_HASH", "your_api_hash_here")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "").strip()

NPV_KEY = b"1234567890123456"  
NPV_IV = b"1234567890123456"   

NPV_EXTENSIONS = ('.npv', '.npvt')
TXT_EXTENSIONS = ('.txt',)

V2RAY_REGEX = r'(?:vless|vmess|trojan|ss|ssr)://[^\s"\'`<>]+'

# ----------------------------------------
# لیست کامل و جامع کانال‌های هدف شما
# ----------------------------------------
CHANNELS = [
    'Azadnet', 'AR14N24B', 'aristapnel', 'arshia_mod_fun', 'canfing_vpn', 
    'capoit', 'configfa', 'configraygan', 'fg_link', 'freenet_vt', 
    'hamedvpns', 'iphone02016vpn', 'irancpi_vpn', 'marambashi', 'merlinvpn', 
    'myporoxy', 'netaccount', 'persianvpnhub', 'pewezavpn', 'proxydaemi', 
    'proxyskull', 'rahgozar94725_ip', 'sinavm', 'soskeynet', 'tikvpnir', 
    'v2freehub', 'wiki_tajrobe', 'xsfilternet', 'yebekhe', 'Cygag', 'DailyV2RY', 
    'v2ray_configs_pools', 'v2rayvpnchannel', 'Galax_vpn', 'v2makers', 'FREE_V2RAYS', 
    'AchaVPN', 'v2ray_free_conf', 'vpnbuying', 'v2rayfori', 'v_ngfree', 'ehsawn8', 
    'V2Shop_Com', 'oneclickvpnkeys', 'NETMelliAnti', 'V2rayngSeven', 'proxy_Shadowsocks', 
    'FreeConfigV2ray_1', 'v2rayfresh', 'v2ray_youtube_group/10', 'v2rayfreedaily', 'outlineOpenKey', 
    'PrivateVPNs', 'VlessConfig', 'vmessiraan', 'vmesskhodam', 'vmessh', 'config_ss', 'config_v2ray_daily', 
    'prrofile_purple', 'v2_mod_shop', 'anty_filter', 'YamYamProxy', 'ettehad_vpn', 'DarkTeam_VPN', 'iran_v2ray1', 
    'samiotech', 'Hope_Net', 'ProxyFa10', 'NEW_MTProxi2', 'proxytel_fast', 'Fr33C0nfig', 'customv2ray', 
    'v2Line', 'GozargahVPN', 'v2raycollector', 'taynnovpn', 'NIM_VPN_ir', 'ShadowProxy66', 'FalconPolV2rayNG', 
    'CUSTOMVPNSERVER', 'lrnbymaa', 'nofiltering2', 'MTproxy22_v2ray', 'Spotify_Porteghali', 'lightning6', 
    'shaxhabb', 'meliproxyy', 'ProxyMTProto', 'LonUp_M', 'sorenab2', 'iMTProto', 'v2rayngvpn', 
    'ConfigX2ray', 'IraneAzad_Net', 'V2WRAY', 'TelMTProto', 'v2ryNG01', 'V2ray_official', 'TheAnilad', 
    'ProxyDotNet', 'NPROXY', 'mrsoulb', 'ConfigsHUB', 'orange_vpns', 'BugFreeNet', 'TeleProxyTele', 
    'iproxy_Meli', 'SimChin_ir', 'V2rayEnglish', 'v2nova8', 'qpshow', 'DarkHub_VPN', 'configmax', 
    'nufilter', 'V2RAY_SPATIAL', 'PulseStore_ir', 'isubvpn', 'Blue_star_Vip', 'Maznet', 'cpy_teeL', 
    'beshcan', 'Parsashonam', 'ProxySnipe', 'Merlin_ViP', 'ghalagyann', 'Free_Nettm', 'EzAccess1', 
    'ChinaPortGFW', 'filshekan_vip', 'ProxyPJ', 'ShabrangVPN', 'V2Ray_Tz', 'acccrd', 'DSR_TM', 
    'BestProxyTel1', 'configshere', 'VpnQavi', 'v2ray_dalghak', 'v2rayng_fars', 'saka_net', 'config_npv', 
    'Outline_vpn', 'freakconfig', 'flyv2ray', 'PROXIS_FREE', 'chatnakonn', 'proxyxix', 'letsproxys', 
    'proxyy_1404', 'duckvp_n', '+JtInm8-guq41OTJi', 'proxy_kafee', 'WizProxy', 'singbox1', 'Farsroid_Club', 
    'filter_breaker', 'taziyanteam', 'V2rayGulf', 'VIPV2rayNGNP', 'oliver_soul', 'internetAzad_Pro', 
    'wibeofme', 'Thirty_secunds', 'herwonderland', 'iDeathBirth', 'training_apks', 'UnNurmal', 
    'config_salavatii', 'Frenpv', 'oxnet_ir', 'pingseven', 'erfanandroid'
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
                if 'config' in js: encrypted_text = js['config']
                elif 'data' in js: encrypted_text = js['data']
            except Exception: pass

        tokens = encrypted_text.split()
        best_token = ""
        max_len = 0
        for t in tokens:
            t = t.replace('-', '+').replace('_', '/')
            cleaned = re.sub(r'[^A-Za-z0-9+/]', '', t)
            if len(cleaned) > max_len:
                max_len = len(cleaned)
                best_token = cleaned

        if max_len < 20: return []
        if len(best_token) % 4 == 1: best_token = best_token[:-1]

        missing_padding = len(best_token) % 4
        if missing_padding: best_token += '=' * (4 - missing_padding)
            
        try:
            encrypted_bytes = base64.b64decode(best_token)
        except Exception: return []
        
        try:
            plain_str = encrypted_bytes.decode('utf-8', errors='strict')
            if '{' in plain_str or '://' in plain_str:
                return re.findall(V2RAY_REGEX, plain_str, re.IGNORECASE)
        except Exception: pass

        if len(encrypted_bytes) % 16 != 0:
            try:
                raw_test = encrypted_bytes.decode('utf-8', errors='ignore')
                return re.findall(V2RAY_REGEX, raw_test, re.IGNORECASE)
            except Exception: return []

        try:
            cipher = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            decrypted_str = decrypted_bytes.decode('utf-8', errors='ignore')
            return re.findall(V2RAY_REGEX, decrypted_str, re.IGNORECASE)
        except Exception:
            try:
                cipher_bypass = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
                raw_decrypted = cipher_bypass.decrypt(encrypted_bytes).decode('utf-8', errors='ignore')
                return re.findall(V2RAY_REGEX, raw_decrypted, re.IGNORECASE)
            except Exception: return []
    except Exception: return []

# ----------------------------------------
# تابع اصلی اسکرپر و ارتباط با تلگرام
# ----------------------------------------
async def main():
    extracted_configs = set()
    # دتکتور آماری برای ذخیره تعداد کانفیگ‌های هر کانال
    channel_stats = {}
    
    if not SESSION_STRING:
        print("\n[❌ ERROR] TELEGRAM_SESSION is empty!")
        return

    print("Connecting to Telegram client...")
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.connect()
    except Exception as init_err:
        print(f"[❌ TELETHON CRASH] Error: {init_err}")
        return
    
    if not await client.is_user_authorized():
        print("[❌ ERROR] Telegram client is not authorized!")
        return

    print(f"Authorization successful. Starting Deep Scan on {len(CHANNELS)} channels...")

    for channel in CHANNELS:
        print(f"Scanning target channel: @{channel}")
        channel_configs_count = 0
        
        try:
            async for message in client.iter_messages(channel, limit=50):
                # ست موقت برای شمارش کانفیگ‌های منحصر به فرد همین پیام/کانال
                current_msg_configs = set()
                
                # لایه اول: متن معمولی پیام
                if message.text:
                    raw_links = re.findall(V2RAY_REGEX, message.text, re.IGNORECASE)
                    for link in raw_links:
                        current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                
                # لایه دوم: هایپرلینک‌های متنی مخفی
                if message.entities:
                    for entity in message.entities:
                        if isinstance(entity, MessageEntityTextUrl) and entity.url:
                            hidden_links = re.findall(V2RAY_REGEX, entity.url, re.IGNORECASE)
                            for link in hidden_links:
                                current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                                
                # لایه سوم: لینک‌های درون دکمه‌های شیشه‌ای
                if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
                    for row in message.reply_markup.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonUrl) and button.url:
                                button_links = re.findall(V2RAY_REGEX, button.url, re.IGNORECASE)
                                for link in button_links:
                                    current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))

                # پارت دوم: اسکن فایل‌های پیوستی
                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    
                    if file_name.endswith(NPV_EXTENSIONS):
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                npv_content = f.read()
                                for link in decrypt_npv_data(npv_content):
                                    current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                        except Exception: pass
                        finally:
                            if os.path.exists(path): os.remove(path)
                                
                    elif file_name.endswith(TXT_EXTENSIONS):
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                txt_content = f.read()
                                txt_links = re.findall(V2RAY_REGEX, txt_content, re.IGNORECASE)
                                for link in txt_links:
                                    current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                        except Exception: pass
                        finally:
                            if os.path.exists(path): os.remove(path)
                
                # اضافه کردن به کلکتور اصلی و شمارش آمار کانال
                for config in current_msg_configs:
                    if config not in extracted_configs:
                        extracted_configs.add(config)
                        channel_configs_count += 1
                        
            # ثبت نهایی آمار این کانال
            channel_stats[channel] = channel_configs_count
                                
        except Exception as chan_err:
            print(f"Could not scan channel {channel}: {chan_err}")
            channel_stats[channel] = "Error/Failed"

    # ----------------------------------------
    # گزارش‌دهی نهایی و ساخت جدول آمار در لاگ
    # ----------------------------------------
    print("\n" + "="*50)
    print("📊 DETAILED CHANNEL EXTRACTION REPORT 📊")
    print("="*50)
    # مرتب‌سازی چنل‌ها بر اساس بیشترین تعداد کانفیگ استخراج شده
    sorted_stats = sorted(channel_stats.items(), key=lambda x: x[1] if isinstance(x[1], int) else -1, reverse=True)
    
    for ch_name, count in sorted_stats:
        print(f"🔹 @{ch_name:<30} -> {count} New Configs")
    print("="*50)
    print(f"✨ Total Unique Configs Collected Globally: {len(extracted_configs)}")
    print("="*50 + "\n")
    
    # ذخیره در فایل خروجی پروژه
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
