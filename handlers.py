"""
Telegram bot handlers module.
Contains all event handlers for the bot.
"""

import os
import re
import logging
from typing import Dict
from telethon import events
from telethon.tl.types import MessageMediaPhoto

from config import CHANNEL_ID
from models import (
    UserData, JENIS_USAHA, INTERNET_OPTIONS, 
    KECEPATAN_OPTIONS, BIAYA_OPTIONS
)
from database import get_user_credentials, save_to_spreadsheet, get_user_records
from storage import upload_to_supabase
from utils import (
    create_buttons, extract_coords_from_gmaps_link,
    format_user_data_summary, format_channel_message,
    format_user_records, format_welcome_message
)

logger = logging.getLogger(__name__)

# Data storage
user_data: Dict[str, UserData] = {}
user_state: Dict[str, str] = {}

def setup_handlers(client):
    """Setup all bot handlers."""
    
    @client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        """Handle /start command."""
        user_id = str(event.sender_id)
        user_state[user_id] = 'started'
        
        credentials = get_user_credentials(user_id)
        if not credentials:
            await event.reply("❌ Anda tidak terdaftar dalam sistem. Hubungi admin.")
            return
        
        welcome_message = format_welcome_message(credentials)
        await event.reply(welcome_message)
    
    @client.on(events.NewMessage(pattern='/add'))
    async def add_handler(event):
        """Handle /add command."""
        user_id = str(event.sender_id)
        
        if user_id not in user_state or user_state[user_id] != 'started':
            await event.reply("Silakan ketik /start terlebih dahulu.")
            return
        
        credentials = get_user_credentials(user_id)
        if not credentials:
            await event.reply("❌ Anda tidak terdaftar dalam sistem. Hubungi admin.")
            return
        
        user_data[user_id] = UserData(user_id, credentials)
        user_state[user_id] = 'adding'
        await event.reply("📝 **Masukkan Nama Usaha:**")
    
    @client.on(events.NewMessage(pattern='/record'))
    async def record_handler(event):
        """Handle /record command."""
        user_id = str(event.sender_id)
        
        if user_id not in user_state or user_state[user_id] != 'started':
            await event.reply("Silakan ketik /start terlebih dahulu.")
            return
        
        records = get_user_records(user_id)
        message = format_user_records(records)
        await event.reply(message)
    
    @client.on(events.NewMessage())
    async def message_handler(event):
        """Handle text messages during data collection."""
        user_id = str(event.sender_id)
        
        if user_id not in user_state:
            await event.reply("Silakan ketik /start terlebih dahulu.")
            return
        
        if user_state.get(user_id) != 'adding':
            return
        
        if event.text and event.text.startswith('/'):
            return
        
        current_data = user_data.get(user_id)
        if not current_data:
            return
        
        current_step = current_data.step
        
        if current_step == 'nama_usaha':
            current_data.nama_usaha = event.text
            current_data.step = 'pic'
            await event.reply("👤 **Masukkan Nama PIC:**")
        
        elif current_step == 'pic':
            current_data.pic = event.text
            current_data.step = 'hpwa'
            await event.reply("📱 **Masukkan Nomor HP/WA:**")
        
        elif current_step == 'hpwa':
            current_data.hpwa = event.text
            current_data.step = 'jenis_usaha'
            buttons = create_buttons(JENIS_USAHA, 'jenis')
            await event.reply("🏭 **Pilih Jenis Usaha:**", buttons=buttons)
        
        elif current_step == 'voc':
            current_data.voc = event.text
            current_data.step = 'location'
            await event.reply("📍 **Kirim Link Google Maps atau share lokasi Anda:**")
    
    @client.on(events.CallbackQuery(data=re.compile(r'jenis_(\d+)')))
    async def jenis_handler(event):
        """Handle jenis usaha button selection."""
        user_id = str(event.sender_id)
        index = int(event.pattern_match.group(1))
        
        if user_id in user_data:
            user_data[user_id].jenis_usaha = JENIS_USAHA[index]
            user_data[user_id].step = 'internet'
            
            buttons = create_buttons(INTERNET_OPTIONS, 'internet')
            await event.edit("🌐 **Pilih Internet Existing:**", buttons=buttons)
    
    @client.on(events.CallbackQuery(data=re.compile(r'internet_(\d+)')))
    async def internet_handler(event):
        """Handle internet option button selection."""
        user_id = str(event.sender_id)
        index = int(event.pattern_match.group(1))
        
        if user_id in user_data:
            user_data[user_id].internet = INTERNET_OPTIONS[index]
            user_data[user_id].step = 'kecepatan'
            
            buttons = create_buttons(KECEPATAN_OPTIONS, 'kecepatan')
            await event.edit("⚡ **Pilih Kecepatan Internet:**", buttons=buttons)
    
    @client.on(events.CallbackQuery(data=re.compile(r'kecepatan_(\d+)')))
    async def kecepatan_handler(event):
        """Handle kecepatan button selection."""
        user_id = str(event.sender_id)
        index = int(event.pattern_match.group(1))
        
        if user_id in user_data:
            user_data[user_id].kecepatan = KECEPATAN_OPTIONS[index]
            user_data[user_id].step = 'biaya'
            
            buttons = create_buttons(BIAYA_OPTIONS, 'biaya')
            await event.edit("💰 **Pilih Range Biaya Internet:**", buttons=buttons)
    
    @client.on(events.CallbackQuery(data=re.compile(r'biaya_(\d+)')))
    async def biaya_handler(event):
        """Handle biaya button selection."""
        user_id = str(event.sender_id)
        index = int(event.pattern_match.group(1))
        
        if user_id in user_data:
            user_data[user_id].biaya = BIAYA_OPTIONS[index]
            user_data[user_id].step = 'voc'
            
            await event.edit("💬 **Masukkan Voice of Customer (VOC):**")
    
    @client.on(events.NewMessage(func=lambda e: hasattr(e.message, "geo") and e.message.geo))
    async def location_handler(event):
        """Handle location sharing."""
        user_id = str(event.sender_id)
        
        if user_id not in user_data or user_data[user_id].step != 'location':
            return
        
        lat = event.message.geo.lat
        lon = event.message.geo.long
        user_data[user_id].location = f"{lat},{lon}"
        user_data[user_id].link_gmaps = f"https://www.google.com/maps?q={lat},{lon}"
        user_data[user_id].step = 'photo'
        
        await event.reply("📸 **Kirim foto:**")
    
    @client.on(events.NewMessage(func=lambda e: 'maps.google.com' in e.text or 'goo.gl/maps' in e.text or 'maps.app.goo.gl' in e.text))
    async def gmaps_handler(event):
        """Handle Google Maps link."""
        user_id = str(event.sender_id)
        
        if user_id not in user_data or user_data[user_id].step != 'location':
            return
        
        user_data[user_id].link_gmaps = event.text
        coords = extract_coords_from_gmaps_link(event.text)
        if coords:
            user_data[user_id].location = coords
            user_data[user_id].step = 'photo'
            await event.reply("📸 **Kirim foto:**")
        else:
            await event.reply("❌ Gagal mengekstrak koordinat dari link. Kirim ulang lokasi Anda.")
    
    @client.on(events.NewMessage(func=lambda e: isinstance(e.message.media, MessageMediaPhoto)))
    async def photo_handler(event):
        """Handle photo upload."""
        user_id = str(event.sender_id)
        
        if user_id not in user_data or user_data[user_id].step not in ['photo', 'complete']:
            return
        
        try:
            # Download and upload photo
            file_path = await event.download_media()
            file_link = upload_to_supabase(file_path)
            user_data[user_id].file_link = file_link
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            file_link = "Gagal upload foto"
        
        # Save data to spreadsheet
        data_dict = user_data[user_id].to_dict()
        if save_to_spreadsheet(data_dict):
            # Send confirmation to user
            summary_message = format_user_data_summary(data_dict)
            await event.reply(summary_message)
            
            # Send notification to channel
            channel_message = format_channel_message(data_dict)
            await client.send_message(CHANNEL_ID, channel_message)
        else:
            await event.reply("❌ Gagal menyimpan data ke spreadsheet")
        
        # Reset user state
        user_state[user_id] = 'started'
        del user_data[user_id]