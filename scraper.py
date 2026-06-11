import re
import os
import json
import base64
import asyncio
import telethon
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

ID_CACHE_FILE = "channel_ids.json"
NPV_KEY = b"1234567890123456"  
NPV_IV = b"1234567890123456"   

NPV_EXTENSIONS = ('.npv', '.npvt')
TXT_EXTENSIONS = ('.txt',)

V2RAY_REGEX = r'(?:vless|vmess|trojan|ss|ssr)://[^\s"\'`<>]+'

# همان لیست بزرگ کانال‌های شما
CHANNELS_LIST = [
    'Azadnet', 'AR14N24B', 'aristapnel', 'Acplus_channel', 'canfing_vpn', 
    'capoit', 'configfa', 'configraygan', 'fg_link', 'freenet_vt', 
    'hamedvpns', 'iphone02016vpn', 'irancpi_vpn', 'marambashi', 'merlinvpn', 
    'myporoxy', 'netaccount', 'persianvpnhub', 'PewezaTech', 'proxydaemi', 
    'proxyskull', 'rahgozar94725_ip', 'sinavm', 'soskeynet', 'tikvpnir', 
    'v2freehub', 'wiki_tajrobe', 'xsfilternet', 'yebekhe', 'Cygag', 'DailyV2RY', 
    'v2ray_configs_pools', 'v2rayvpnchannel', 'Galax_vpn', 'v2makers', 'FREE_V2RAYS', 
    'AchaVPN', 'v2ray_free_conf', 'vpnbuying', 'v2rayfori', 'v_ngfree', 'ehsawn8', 
    'V2Shop_Com', 'oneclickvpnkeys', 'NETMelliAnti', 'V2rayngSeven', 'proxy_Shadowsocks', 
    'FreeConfigV2ray_1', 'v2rayfresh', 'v2ray_youtube_group', 'v2rayfreedaily', 'outlineOpenKey', 
    'PrivateVPNs', 'VlessConfig', 'vmessiraan', 'vmesskhodam', 'vmessh', 'config_ss', 'config_v2ray_daily', 
    'prrofile_purple', 'v2_mod_shop', 'anty_filter', 'YamYamProxy', 'ettehad_vpn', 'DarkTeam_VPN', 'iran_v2ray1', 
    'samiotech', 'Hope_Net', 'ProxyFa10', 'NEW_MTProxi2', 'proxytel_fast', 'Fr33C0nfig', 'customv2ray', 
    'v2Line', 'GozargahVPN', 'v2raycollector', 'taynnovpn', 'NIM_VPN_ir', 'ShadowProxy66', 'FalconPolV2rayNG', 
    'CUSTOMVPNSERVER', 'lrnbymaa', 'nofiltering2', 'MTproxy22_v2ray', 'Spotify_Porteghali', 'lightning6', 
    'Mrshahabx', 'meliproxyy', 'ProxyMTProto', 'LonUp_M', 'sorenab2', 'iMTProto', 'v2rayngvpn', 
    'ConfigX2ray', 'IraneAzad_Net', 'V2WRAY', 'TelMTProto', 'v2ryNG01', 'V2ray_official', 'TheAnilad', 
    'ProxyDotNet', 'NPROXY', 'mrsoulb', 'ConfigsHUB', 'orange_vpns', 'BugFreeNet', 'TeleProxyTele', 
    'iproxy_Meli', 'SimChin_ir', 'V2rayEnglish', 'v2nova8', 'qpshow', 'DarkHub_VPN', 'configmax', 
    'nufilter', 'V2RAY_SPATIAL', 'PulseStore_ir', 'isubvpn', 'Blue_star_Vip', 'Maznet', 'cpy_teeL', 
    'beshcan', 'Parsashonam', 'ProxySnipe', 'Merlin_ViP', 'ghalagyann', 'Free_Nettm', 'EzAccess1', 
    'ByGFW', 'filshekan_vip', 'ProxyPJ', 'ShabrangVPN', 'V2Ray_Tz', 'acccrd', 'DSR_TM', 
    'BestProxyTel1', 'configshere', 'VpnQavi', 'v2ray_dalghak', 'v2rayng_fars', 'saka_net', 'config_npv', 
    'Outline_vpn', 'freakconfig', 'flyv2ray', 'PROXIS_FREE', 'chatnakonn', 'proxyxix', 'letsproxys', 
    'proxyy_1404', 'duckvp_n', '+JtInm8-guq41OTJi', 'proxy_kafee', 'WizProxy', 'singbox1', 'Farsroid_Club', 
    'filter_breaker', 'taziyanteam', 'V2rayGulf', 'VIPV2rayNGNP', 'oliver_soul', 'internetAzad_Pro', 
    'wibeofme', 'Thirty_secunds', 'herwonderland', 'iDeathBirth', 'training_apks', 'UnNurmal', 
    'config_salavatii', 'Frenpv', 'oxnet_ir', 'pingseven', 'erfanandroid'
]

# ----------------------------------------
# توابع لود و سیو دیتابیس آیدی‌ها
# ----------------------------------------
def load_cached_ids():
    if os.path.exists(ID_CACHE_FILE):
        try:
            with open(ID_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
    return {}

def save_cached_ids(cache_data):
    try:
        with open(ID_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save ID cache: {e}")

# (تابع decrypt_npv_data بدون تغییر در این‌جا قرار دارد اما برای خلاصه شدن متن، مستقیم سراغ main می‌رویم)
def decrypt_npv_data(encrypted_text):
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
        try: encrypted_bytes = base64.b64decode(best_token)
        except Exception: return []
        try:
            plain_str = encrypted_bytes.decode('utf-8', errors='strict')
            if '{' in plain_str or '://' in plain_str: return re.findall(V2RAY_REGEX, plain_str, re.IGNORECASE)
        except Exception: pass
        if len(encrypted_bytes) % 16 != 0:
            try: return re.findall(V2RAY_REGEX, encrypted_bytes.decode('utf-8', errors='ignore'), re.IGNORECASE)
            except Exception: return []
        try:
            cipher = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
            return re.findall(V2RAY_REGEX, unpad(cipher.decrypt(encrypted_bytes), AES.block_size).decode('utf-8', errors='ignore'), re.IGNORECASE)
        except Exception:
            try: return re.findall(V2RAY_REGEX, AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV).decrypt(encrypted_bytes).decode('utf-8', errors='ignore'), re.IGNORECASE)
            except Exception: return []
    except Exception: return []

# ----------------------------------------
# تابع اصلی اسکرپر
# ----------------------------------------
async def main():
    extracted_configs = set()
    channel_stats = {}
    
    id_cache = load_cached_ids()
    is_cache_updated = False

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

    print(f"Authorization successful. Scanning {len(CHANNELS_LIST)} channels...")

    for channel_target in CHANNELS_LIST:
        channel_configs_count = 0
        display_name = channel_target
        
        # تعیین نهاد ورودی به تلتون (آیدی عددی یا یوزرنیم متنی)
        entity_to_scan = channel_target
        if channel_target in id_cache:
            entity_to_scan = id_cache[channel_target]
            display_name = f"{channel_target} (via Cache ID: {entity_to_scan})"

        print(f"Processing channel: {display_name}")
        
        try:
            # تاخیر زمانی کوتاه برای امنیت بیشتر
            await asyncio.sleep(2.5)
            
            # گرفتن آیدی عددی و ذخیره آن در کش در صورت جدید بودن
            if channel_target not in id_cache:
                try:
                    input_entity = await client.get_input_entity(channel_target)
                    # استخراج آیدی عددی از شیء تلتون
                    if hasattr(input_entity, 'channel_id'):
                        actual_id = int(f"-100{input_entity.channel_id}")
                        id_cache[channel_target] = actual_id
                        entity_to_scan = actual_id
                        is_cache_updated = True
                        print(f"🎯 Successfully mapped and cached @{channel_target} -> {actual_id}")
                except Exception as entity_err:
                    print(f"[⚠️ WARNING] Could not resolve ID for {channel_target}: {entity_err}")

            # شروع اسکن پیام‌ها با استفاده از آیدی یا متن پایداری که داریم
            async for message in client.iter_messages(entity_to_scan, limit=50):
                current_msg_configs = set()
                
                if message.text:
                    for link in re.findall(V2RAY_REGEX, message.text, re.IGNORECASE):
                        current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                
                if message.entities:
                    for entity in message.entities:
                        if isinstance(entity, MessageEntityTextUrl) and entity.url:
                            for link in re.findall(V2RAY_REGEX, entity.url, re.IGNORECASE):
                                current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                                
                if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
                    for row in message.reply_markup.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonUrl) and button.url:
                                for link in re.findall(V2RAY_REGEX, button.url, re.IGNORECASE):
                                    current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))

                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    if file_name.endswith(NPV_EXTENSIONS):
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                for link in decrypt_npv_data(f.read()):
                                    current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                        except Exception: pass
                        finally:
                            if os.path.exists(path): os.remove(path)
                                
                    elif file_name.endswith(TXT_EXTENSIONS):
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                for link in re.findall(V2RAY_REGEX, f.read(), re.IGNORECASE):
                                    current_msg_configs.add(link.strip().rstrip('.,_`*)]}'))
                        except Exception: pass
                        finally:
                            if os.path.exists(path): os.remove(path)
                
                for config in current_msg_configs:
                    if config not in extracted_configs:
                        extracted_configs.add(config)
                        channel_configs_count += 1
                        
            channel_stats[channel_target] = channel_configs_count
                                
        except telethon.errors.rpcerrorlist.FloodWaitError as flood_err:
            print(f"[⚠️ FLOOD WAIT] Reached restriction. Delay needed: {flood_err.seconds}s on {channel_target}")
            channel_stats[channel_target] = "Skipped (Flood)"
            
        except Exception as chan_err:
            print(f"Could not scan channel {channel_target}: {chan_err}")
            channel_stats[channel_target] = "Error/Failed"

    # ذخیره دیتابیس آیدی‌ها در صورت تغییر
    if is_cache_updated:
        save_cached_ids(id_cache)

    # ----------------------------------------
    # گزارش‌دهی نهایی و داکیومنت کردن خروجی
    # ----------------------------------------
    print("\n" + "="*50)
    print("📊 DETAILED CHANNEL EXTRACTION REPORT 📊")
    print("="*50)
    sorted_stats = sorted(channel_stats.items(), key=lambda x: x[1] if isinstance(x[1], int) else -1, reverse=True)
    for ch_name, count in sorted_stats:
        print(f"🔹 {ch_name:<30} -> {count} New Configs")
    print("="*50)
    print(f"✨ Total Unique Configs Collected Globally: {len(extracted_configs)}")
    print("="*50 + "\n")
    
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
