import os
import re
import json
import gspread
import logging
import requests
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageMediaPhoto
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from supabase import create_client, Client
from timezone_utils import get_current_time, format_timestamp

# Load environment variables
load_dotenv()

def get_env_var(name, required=True):
    value = os.environ.get(name)
    if required and not value:
        raise ValueError(f"{name} environment variable not set!")
    return value

# Environment variables
API_ID = int(get_env_var('API_ID'))
API_HASH = get_env_var('API_HASH')
BOT_TOKEN = get_env_var('BOT_TOKEN')
SHEET_NAME = "Rekap Visit AM"
SUPABASE_URL = get_env_var('SUPABASE_URL', required=False)
SUPABASE_KEY = get_env_var('SUPABASE_KEY', required=False)

# Google credentials
creds_json = get_env_var('GOOGLE_CREDS_JSON')
creds_dict = json.loads(creds_json)
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)
sheet = gc.open(SHEET_NAME).sheet1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Column indices for spreadsheet
COLUMNS = {
    'no': 0,
    'timestamp': 1,
    'user_id': 2,
    'nama_sa': 3,
    'witel': 4,
    'telda': 5,
    'sto': 6,
    'cluster': 7,
    'nama_usaha': 8,
    'jenis_usaha': 9,
    'pic': 10,
    'hpwa': 11,
    'internet': 12,
    'kecepatan': 13,
    'biaya': 14,
    'voc': 15,
    'location': 16,
    'file_link': 17,
    'link_gmaps': 18,
    'validitas': 19
}

# Options for buttons
JENIS_USAHA = [
    "Hotel", "Manufaktur", "Cafe", "Tempat Wisata", 
    "Rumah Sakit", "Sekolah", "Industri", "Distributor", "Pergudangan"
]

INTERNET_OPTIONS = [
    "IndiHome", "Indibiz", "Biznet", "First Media", 
    "MNC Play", "MyRepublic", "Oxygen", "CBN", 
    "XL Home", "Indosat GIG", "Iconnet", "ISP Lokal"
]

KECEPATAN_OPTIONS = [
    "10-50 Mbps", "50-75 Mbps", "75-100 Mbps", ">100 Mbps"
]

BIAYA_OPTIONS = [
    "<200.000", "200.000-300.000", 
    "300.000-400.000", "400.000-700.000", ">700.000"
]

# Data storage
user_data = {}
user_state = {}

# Initialize client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Get user credentials from Google Sheet
def get_user_credentials(user_id: str) -> Optional[Dict]:
    """Get user credentials from Google Sheet"""
    try:
        credentials_sheet = gc.open(SHEET_NAME).worksheet("Credentials")
        records = credentials_sheet.get_all_records()
        for record in records:
            if str(record.get('Telegram ID')) == str(user_id):
                return {
                    'kode': record.get('Kode SA'),
                    'nama_sa': record.get('Nama'),
                    'witel': record.get('Witel'),
                    'telda': record.get('Telda'),
                    'sto': record.get('STO'),
                    'cluster': record.get('Cluster')
                }
        return None
    except Exception as e:
        logger.error(f"Error getting user credentials: {e}")
        return None

# Create inline buttons from options
def create_buttons(options: List[str], prefix: str) -> List[List[Button]]:
    """Create inline buttons from options"""
    buttons = []
    row = []
    for i, option in enumerate(options):
        row.append(Button.inline(option, f"{prefix}_{i}"))
        if len(row) == 2 or i == len(options) - 1:
            buttons.append(row)
            row = []
    return buttons

# Upload file to Supabase storage
def upload_to_supabase(file_path: str) -> str:
    """Upload file to Supabase storage"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return "Foto tersimpan (tanpa upload)"
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        file_extension = os.path.splitext(file_path)[1]
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        bucket_name = "photo"
        response = supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=file_data,
            file_options={"content-type": "image/jpeg"}
        )
        
        if response:
            public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
            return public_url
        return "Foto tersimpan (gagal upload)"
    except Exception as e:
        logger.error(f"Supabase upload error: {e}")
        return "Foto tersimpan (error sistem)"

# Save data to Google Sheet
def save_to_spreadsheet(data: Dict) -> bool:
    """Save data to spreadsheet"""
    try:
        timestamp = format_timestamp()
        no = len(sheet.get_all_values())
        
        row_data = [
            no, timestamp, data['user_id'], data['nama_sa'], data['witel'], data['telda'], data['sto'], 
            data['cluster'], data['nama_usaha'], data['jenis_usaha'], 
            data['pic'], data['hpwa'], data['internet'], data['kecepatan'], 
            data['biaya'], data['voc'], data.get('location', ''), 
            data.get('file_link', ''), data.get('link_gmaps', ''), "Default"
        ]
        
        sheet.append_row(row_data)
        return True
    except Exception as e:
        logger.error(f"Failed to save to spreadsheet: {e}")
        return False

# Get user's previous records from spreadsheet
def get_user_records(user_id: str) -> List[Dict]:
    """Get user's previous records from spreadsheet"""
    try:
        records = sheet.get_all_records()
        user_records = []
        for record in records:
            if str(record.get('ID')) == str(user_id):
                user_records.append({
                    'no': record.get('No'),
                    'nama_usaha': record.get('Nama Usaha'),
                    'PIC': record.get('PIC'),
                    'hpwa': record.get('HP/WA'),
                    'timestamp': record.get('Timestamp')
                })
        return user_records
    except Exception as e:
        logger.error(f"Error getting user records: {e}")
        return []

# Extract coordinates from Google Maps link
def extract_coords_from_gmaps_link(link: str) -> Optional[str]:
    """Extract latitude and longitude from Google Maps link, including shortlinks."""
    if not link or not link.strip():
        return None
    try:
        # 1. Cek langsung di link (jarang, tapi bisa saja)
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
        if match:
            lat, lng = match.groups()
            return f"{lat},{lng}"
        # 2. Cek pola q=lat,lon di link
        match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', link)
        if match:
            lat, lng = match.groups()
            return f"{lat},{lng}"
        # 3. Jika shortlink, resolve dan cek redirect
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(link, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url
        # Cek pola @lat,lon di final_url
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if match:
            lat, lng = match.groups()
            return f"{lat},{lng}"
        # Cek pola q=lat,lon di final_url
        match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if match:
            lat, lng = match.groups()
            return f"{lat},{lng}"
        # Cek di response.text (kadang ada di HTML)
        match = re.search(r'(-?\d+\.\d+),(-?\d+\.\d+)', response.text)
        if match:
            lat, lng = match.groups()
            return f"{lat},{lng}"
    except Exception as e:
        logger.error(f"Error extracting coordinates from link {link}: {e}")
    return None

# Command handlers
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = str(event.sender_id)
    user_state[user_id] = 'started'
    
    credentials = get_user_credentials(user_id)
    if not credentials:
        await event.reply("❌ Anda tidak terdaftar dalam sistem. Hubungi admin.")
        return
    
    await event.reply(
        f"🤖 **Selamat datang {credentials['nama_sa']}!**\n\n"
        f"Witel: {credentials['witel']}\n"
        f"Telda: {credentials['telda']}\n"
        f"Cluster: {credentials['cluster']}\n\n"
        f"STO: {credentials['sto']}\n\n"
        "Ketik /add untuk menambahkan data baru atau /record untuk melihat data sebelumnya."
    )

# Add handler
@client.on(events.NewMessage(pattern='/add'))
async def add_handler(event):
    user_id = str(event.sender_id)
    
    if user_id not in user_state or user_state[user_id] != 'started':
        await event.reply("Silakan ketik /start terlebih dahulu.")
        return
    
    credentials = get_user_credentials(user_id)
    if not credentials:
        await event.reply("❌ Anda tidak terdaftar dalam sistem. Hubungi admin.")
        return
    
    user_data[user_id] = {
        'user_id': user_id,
        'nama_sa': credentials['nama_sa'],
        'sto': credentials['sto'],
        'witel': credentials['witel'],
        'telda': credentials['telda'],
        'cluster': credentials['cluster'],
        'step': 'nama_usaha'
    }
    
    user_state[user_id] = 'adding'
    await event.reply("📝 **Masukkan Nama Usaha:**")

# Record handler
@client.on(events.NewMessage(pattern='/record'))
async def record_handler(event):
    user_id = str(event.sender_id)
    
    if user_id not in user_state or user_state[user_id] != 'started':
        await event.reply("Silakan ketik /start terlebih dahulu.")
        return
    
    records = get_user_records(user_id)
    if not records:
        await event.reply("📭 Anda belum memiliki data yang tersimpan.")
        return
    
    message = "📋 **Data yang pernah Anda input:**\n\n"
    for record in records:
        message += f"🔹 No: {record['no']}\n"
        message += f"🏢 Usaha: {record['nama_usaha']}\n"
        message += f"👤 PIC: {record['PIC']}\n"
        message += f"📱 HP/WA: {record['hpwa']}\n"
        message += f"📅 Waktu: {record['timestamp']}\n\n"
    
    await event.reply(message)

# Message handlers
@client.on(events.NewMessage())
async def message_handler(event):
    user_id = str(event.sender_id)
    
    if user_id not in user_state:
        await event.reply("Silakan ketik /start terlebih dahulu.")
        return
    
    if user_state.get(user_id) != 'adding':
        return
    
    if event.text and event.text.startswith('/'):
        return
    
    current_data = user_data.get(user_id, {})
    current_step = current_data.get('step')
    
    if current_step == 'nama_usaha':
        user_data[user_id]['nama_usaha'] = event.text
        user_data[user_id]['step'] = 'pic'
        await event.reply("👤 **Masukkan Nama PIC:**")
    
    elif current_step == 'pic':
        user_data[user_id]['pic'] = event.text
        user_data[user_id]['step'] = 'hpwa'
        await event.reply("📱 **Masukkan Nomor HP/WA:**")
    
    elif current_step == 'hpwa':
        user_data[user_id]['hpwa'] = event.text
        user_data[user_id]['step'] = 'jenis_usaha'
        buttons = create_buttons(JENIS_USAHA, 'jenis')
        await event.reply("🏭 **Pilih Jenis Usaha:**", buttons=buttons)
    
    elif current_step == 'voc':
        user_data[user_id]['voc'] = event.text
        user_data[user_id]['step'] = 'location'
        await event.reply("📍 **Kirim Link Google Maps atau share lokasi Anda:**")

# Button handlers
@client.on(events.CallbackQuery(data=re.compile(r'jenis_(\d+)')))
async def jenis_handler(event):
    user_id = str(event.sender_id)
    index = int(event.pattern_match.group(1))
    
    user_data[user_id]['jenis_usaha'] = JENIS_USAHA[index]
    user_data[user_id]['step'] = 'internet'
    
    buttons = create_buttons(INTERNET_OPTIONS, 'internet')
    await event.edit("🌐 **Pilih Internet Existing:**", buttons=buttons)

# Internet handler
@client.on(events.CallbackQuery(data=re.compile(r'internet_(\d+)')))
async def internet_handler(event):
    user_id = str(event.sender_id)
    index = int(event.pattern_match.group(1))
    
    user_data[user_id]['internet'] = INTERNET_OPTIONS[index]
    user_data[user_id]['step'] = 'kecepatan'
    
    buttons = create_buttons(KECEPATAN_OPTIONS, 'kecepatan')
    await event.edit("⚡ **Pilih Kecepatan Internet:**", buttons=buttons)

# Kecepatan handler
@client.on(events.CallbackQuery(data=re.compile(r'kecepatan_(\d+)')))
async def kecepatan_handler(event):
    user_id = str(event.sender_id)
    index = int(event.pattern_match.group(1))
    
    user_data[user_id]['kecepatan'] = KECEPATAN_OPTIONS[index]
    user_data[user_id]['step'] = 'biaya'
    
    buttons = create_buttons(BIAYA_OPTIONS, 'biaya')
    await event.edit("💰 **Pilih Range Biaya Internet:**", buttons=buttons)

#  Biaya handler
@client.on(events.CallbackQuery(data=re.compile(r'biaya_(\d+)')))
async def biaya_handler(event):
    user_id = str(event.sender_id)
    index = int(event.pattern_match.group(1))
    
    user_data[user_id]['biaya'] = BIAYA_OPTIONS[index]
    user_data[user_id]['step'] = 'voc'
    
    await event.edit("💬 **Masukkan Voice of Customer (VOC):**")

# Location and photo handlers
@client.on(events.NewMessage(func=lambda e: hasattr(e.message, "geo") and e.message.geo))
async def location_handler(event):
    user_id = str(event.sender_id)
    
    if user_id not in user_data or user_data[user_id].get('step') != 'location':
        return
    
    lat = event.message.geo.lat
    lon = event.message.geo.long
    user_data[user_id]['location'] = f"{lat},{lon}"
    user_data[user_id]['link_gmaps'] = f"https://www.google.com/maps?q={lat},{lon}"
    user_data[user_id]['step'] = 'photo'
    
    await event.reply("📸 **Kirim foto:**")

# Google Maps link handler
@client.on(events.NewMessage(func=lambda e: 'maps.google.com' in e.text or 'goo.gl/maps' in e.text or 'maps.app.goo.gl' in e.text))
async def gmaps_handler(event):
    user_id = str(event.sender_id)
    
    if user_id not in user_data or user_data[user_id].get('step') != 'location':
        return
    
    user_data[user_id]['link_gmaps'] = event.text
    coords = extract_coords_from_gmaps_link(event.text)
    if coords:
        user_data[user_id]['location'] = coords
        user_data[user_id]['step'] = 'photo'  # <-- Tambahkan baris ini!
        await event.reply("📸 **Kirim foto:**")
    else:
        await event.reply("❌ Gagal mengekstrak koordinat dari link. Kirim ulang lokasi Anda.")

# Photo upload handler
@client.on(events.NewMessage(func=lambda e: isinstance(e.message.media, MessageMediaPhoto)))
async def photo_handler(event):
    user_id = str(event.sender_id)
    
    if user_id not in user_data or user_data[user_id].get('step') not in ['photo', 'complete']:
        return
    
    try:
        file_path = await event.download_media()
        file_link = upload_to_supabase(file_path)
        user_data[user_id]['file_link'] = file_link
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        file_link = "Gagal upload foto"
    
    # Save data to spreadsheet
    if save_to_spreadsheet(user_data[user_id]):
        await event.reply(
            f"✅ **Data berhasil disimpan!**\n\n"
            f"🏢 Usaha: {user_data[user_id]['nama_usaha']}\n"
            f"👤 PIC: {user_data[user_id]['pic']}\n"
            f"📱 HP/WA: {user_data[user_id]['hpwa']}\n"
            f"🏭 Jenis Usaha: {user_data[user_id]['jenis_usaha']}\n"
            f"🌐 Internet: {user_data[user_id]['internet']}\n"
            f"⚡ Kecepatan: {user_data[user_id]['kecepatan']}\n"
            f"💰 Biaya: {user_data[user_id]['biaya']}\n"
            f"💬 VOC: {user_data[user_id]['voc']}\n"
            f"📍 Lokasi: {user_data[user_id].get('location', 'Tidak ada')}\n"
            f"📊 Data telah ditambahkan ke spreadsheet"
        )
        # Kirim ke channel
        channel_id = -1002591459174  # Ganti dengan ID/username channel Anda
        pesan_channel = (
            f"📢 Data baru masuk!\n\n"
            f"Nama SA: {user_data[user_id]['nama_sa']}\n"
            f"Witel: {user_data[user_id]['witel']}\n"
            f"Telda: {user_data[user_id]['telda']}\n\n"
            f"🏢 Usaha: {user_data[user_id]['nama_usaha']}\n"
            f"👤 PIC: {user_data[user_id]['pic']}\n\n"
            f"📎 Foto: {user_data[user_id].get('file_link', '-')}\n"
        )
        await client.send_message(channel_id, pesan_channel)
    else:
        await event.reply("❌ Gagal menyimpan data ke spreadsheet")
    
    # Reset user state
    user_state[user_id] = 'started'
    del user_data[user_id]

# Run the bot
if __name__ == "__main__":
    logger.info("Bot is starting...")
    client.run_until_disconnected()