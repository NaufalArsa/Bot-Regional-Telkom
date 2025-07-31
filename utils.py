"""
Utility functions for the Telegram bot.
Contains helper functions for coordinate extraction, button creation, etc.
"""

import re
import requests
import logging
from typing import List, Optional, Tuple
from telethon import Button

logger = logging.getLogger(__name__)

def create_buttons(options: List[str], prefix: str) -> List[List[Button]]:
    """Create inline buttons from options."""
    buttons = []
    row = []
    for i, option in enumerate(options):
        row.append(Button.inline(option, f"{prefix}_{i}"))
        if len(row) == 2 or i == len(options) - 1:
            buttons.append(row)
            row = []
    return buttons

def extract_coords_from_gmaps_link(link: str) -> Tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude from Google Maps short or long link."""
    if not link or not link.strip():
        return None, None
    try:
        # follow redirects to get the final URL page
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(link, headers=headers, allow_redirects=True, timeout=50)
        html = response.text
        # Try to extract lat,lng from embed or preview URLs
        match = re.search(
            r"https://www\.google\.com/maps/preview/place/.*?@(-?\d+\.\d+),(-?\d+\.\d+)",
            html
        )
        if match:
            lat, lng = match.groups()
            return float(lat), float(lng)
        # fallback: try plain lat,lng patterns in URL or page
        full_url = response.url
        match2 = re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", full_url)
        if match2:
            lat, lng = match2.groups()
            return float(lat), float(lng)
    except Exception as e:
        logger.error(f"Error extracting coordinates from link {link}: {e}")
    
    return None, None

def format_user_data_summary(data: dict) -> str:
    """Format user data for display in confirmation message."""
    return (
        f"✅ **Data berhasil disimpan!**\n\n"
        f"🏢 Usaha: {data['nama_usaha']}\n"
        f"👤 PIC: {data['pic']}\n"
        f"🪪 Status PIC: {data.get('status_pic', 'Tidak ada')}\n"
        f"📱 HP/WA: {data['hpwa']}\n"
        f"🏭 Jenis Usaha: {data['jenis_usaha']}\n"
        f"🌐 Internet: {data['internet']}\n"
        f"⚡ Kecepatan: {data['kecepatan']}\n"
        f"💰 Biaya: {data['biaya']}\n"
        f"💬 VOC: {data['voc']}\n"
        f"📍 Lokasi: {data.get('location', 'Tidak ada')}\n"
        f"🏢 STO: {data.get('sto', 'Tidak ada')}\n"
        f"🚩 ODP: {data.get('odp', 'Tidak ada')}\n"
        f"📊 Data telah ditambahkan ke spreadsheet"
    )

def format_channel_message(data: dict) -> str:
    """Format message for channel notification."""
    return (
        f"📢 Data baru masuk!\n\n"
        f"Nama SA: {data['nama_sa']}\n"
        f"Witel: {data['witel']}\n"
        f"Telda: {data['telda']}\n\n"
        f"🏢 Usaha: {data['nama_usaha']}\n"
        f"👤 PIC: {data['pic']}\n\n"
        f"📎 Foto: {data.get('file_link', '-')}\n"
    )

def format_user_records(records: List[dict]) -> str:
    """Format user's previous records for display."""
    if not records:
        return "📭 Anda belum memiliki data yang tersimpan."
    
    message = "📋 **Data yang pernah Anda input:**\n\n"
    for record in records:
        message += f"🔹 No: {record['no']}\n"
        message += f"🏢 Usaha: {record['nama_usaha']}\n"
        message += f"👤 PIC: {record['pic']}\n"
        message += f"📅 Waktu: {record['timestamp']}\n\n"
    
    return message

def format_welcome_message(credentials: dict) -> str:
    """Format welcome message with user credentials."""
    return (
        f"🤖 **Selamat datang {credentials['nama_sa']}!**\n\n"
        f"Witel: {credentials['witel']}\n"
        f"Telda: {credentials['telda']}\n\n"
        f"Command yang tersedia:\n"
        f"• /add: Tambah data usaha baru\n"
        f"• /record: Lihat data usaha yang pernah Anda input\n" 
        f"• /odp: Cari ODP terdekat\n"
    )