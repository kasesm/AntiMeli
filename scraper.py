import re
import os
import json
import base64
import asyncio  # 👈 این خطِ جا افتاده را اضافه کن
from telethon import TelegramClient
from telethon.sessions import StringSession
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# دریافت اطلاعات حساس از سکرت‌های گیت‌هاب
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("TG_SESSION_STRING")

# لیست کانال‌های هدف
TARGET_CHANNELS = [
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

V2RAY_REGEX = r'(vless|vmess|trojan|ss|ssr)://[^\s]+'
OUTPUT_FILE = "sub_link.txt"
NPV_EXTENSIONS = ('.npv', '.npvt')

# کلید پیش‌فرض و استاندارد معماری نپسترنت کلاینت (قابل تغییر بر حسب ورژن اپلیکیشن چنل‌ها)
# این کلید ۳۲ بایتی برای رمزگشایی AES-256 استفاده می‌شود
NPV_KEY = b'NapsternetVBestV2rayClientForAnd' 
NPV_IV = b'0123456789abcdef' # IV استاندارد ۱۶ بایتی پیش‌فرض

def decrypt_npv_data(encrypted_text):
    """رمزگشایی محلی فایل نپسترنت و استخراج لینک‌های مستقیم V2Ray"""
    try:
        # ۱. باز کردن ساختار Base64 اولیه فایل
        encrypted_bytes = base64.b64decode(encrypted_text.strip())
        
        # ۲. پیکربندی موتور رمزگشایی AES در حالت CBC
        cipher = AES.new(NPV_KEY, AES.MODE_CBC, NPV_IV)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        decrypted_str = decrypted_bytes.decode('utf-8', errors='ignore')
        
        # ۳. پیدا کردن لینک‌های رسمی v2ray از داخل دیتای رمزگشایی شده (متن یا ساختار JSON)
        found_links = re.findall(V2RAY_REGEX, decrypted_str, re.IGNORECASE)
        return found_links
    except Exception as e:
        # اگر فرمت قفل متفاوتی در ورژن‌های خاص استفاده شده باشد، این بخش خطا را رد می‌کند
        print(f"Local Decryption Failed: {e}")
        return []

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
            # اسکن سریع ۵۰ پیام اخیر (چون سرعت بالا رفته و خطر بلاک نداریم، لیمیت را افزایش دادیم)
            async for message in client.iter_messages(target, limit=50):
                
                # پارت اول: جمع‌آوری لینک‌های مستقیم متنی از چنل
                if message.text:
                    v2ray_matches = re.findall(V2RAY_REGEX, message.text, re.IGNORECASE)
                    for match in v2ray_matches:
                        extracted_configs.add(match.strip())

                # پارت دوم: دانلود و رمزگشایی اختصاصی فایل‌های نپسترنت
                if message.file and message.file.name:
                    file_name = message.file.name.lower()
                    
                    if file_name.endswith(NPV_EXTENSIONS):
                        print(f"Found NapsternetV file: {file_name}. Processing locally...")
                        path = await message.download_media()
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                npv_content = f.read()
                                # صدا زدن تابع دیکودر محلی
                                local_links = decrypt_npv_data(npv_content)
                                for link in local_links:
                                    print(f"Successfully decrypted from NPV: {link[:30]}...")
                                    extracted_configs.add(link.strip())
                        except Exception as file_err:
                            print(f"Error processing file {file_name}: {file_err}")
                        finally:
                            if os.path.exists(path):
                                os.remove(path)

        except Exception as e:
            print(f"Error accessing {target}: {e}")

    # ذخیره نهایی تمام کانفیگ‌های یکتا در فایل سابلینک
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for config in sorted(extracted_configs):
            f.write(config + "\n")

    await client.disconnect()
    print("Scraping and local NPV decryption finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
