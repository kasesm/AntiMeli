import re
import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# دریافت اطلاعات حساس از سکرت‌های گیت‌هاب
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("TG_SESSION_STRING")

# لیست کانال‌ها و گروه‌های هدف برای جمع‌آوری کانفیگ (ددوپلیکیت و تمیز شده)
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

DECRYPTOR_BOT = '@DickiriptorBot'
BUTTON_TEXT_TARGET = "لینک ویتوریش رو بده"

V2RAY_REGEX = r'(vless|vmess|trojan|ss|ssr)://[^\s]+'
OUTPUT_FILE = "sub_link.txt"
CUSTOM_EXTENSIONS = ('.ehi', '.npv', '.npvt', '.ovpn', '.nm', '.slp', '.tnl', '.rk', '.happ')

async def main():
    extracted_configs = set()

    # بارگذاری کانفیگ‌های قبلی برای جلوگیری از حذف شدن آنها
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
            # بررسی ۵۰ پیام اخیر کانال/گروه
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
                            await asyncio.sleep(4) # انتظار برای ارسال دکمه‌ها از سمت ربات
                            
                            # دریافت آخرین پیام حاوی دکمه‌های شیشه‌ای از ربات
                            async for bot_msg in client.iter_messages(DECRYPTOR_BOT, limit=1):
                                if bot_msg.buttons:
                                    button_clicked = False
                                    
                                    # جستجو در میان دکمه‌های شیشه‌ای پیام
                                    for row in bot_msg.buttons:
                                        for button in row:
                                            if BUTTON_TEXT_TARGET in button.text or "لینک ویتوری" in button.text:
                                                print(f"Clicking inline button: '{button.text}'")
                                                await button.click()
                                                button_clicked = True
                                                break
                                        if button_clicked:
                                            break
                                    
                                    if button_clicked:
                                        await asyncio.sleep(4) # انتظار برای دریافت لینک بعد از کلیک روی دکمه
                                        
                                        # خواندن پیام جدید حاوی لینک v2ray مستقیم
                                        async for link_msg in client.iter_messages(DECRYPTOR_BOT, limit=1):
                                            if link_msg.text:
                                                bot_v2ray = re.findall(V2RAY_REGEX, link_msg.text, re.IGNORECASE)
                                                for match in bot_v2ray:
                                                    print(f"Extracted from button: {match[:30]}...")
                                                    extracted_configs.add(match.strip())
                        except Exception as bot_err:
                            print(f"Error during button interaction: {bot_err}")

        except Exception as e:
            # اگر کانالی دیلیت شده بود یا اکانت شما در آن گروه عضو نبود، اسکریپت کرش نمی‌کند و به کارش ادامه می‌دهد
            print(f"Error accessing {target}: {e}")

    # ذخیره نهایی تمام کانفیگ‌های منحصر به فرد در سابلینک
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for config in sorted(extracted_configs):
            f.write(config + "\n")

    await client.disconnect()
    print("Scraping workflow finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
