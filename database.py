"""
Database operations module for Google Sheets integration.
Handles user credentials, data storage, and record retrieval.
"""

import gspread
import logging
from typing import Dict, Optional, List
from oauth2client.service_account import ServiceAccountCredentials
from config import get_google_credentials_dict, GOOGLE_SCOPE, SHEET_NAME
from models import UserCredentials, UserRecord
from timezone_utils import format_timestamp

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Manages Google Sheets operations."""
    
    def __init__(self):
        """Initialize Google Sheets client."""
        self.creds_dict = get_google_credentials_dict()
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(
            self.creds_dict, GOOGLE_SCOPE
        )
        self.gc = gspread.authorize(self.creds)
        self.sheet = self.gc.open(SHEET_NAME).sheet1
    
    def get_user_credentials(self, user_id: str) -> Optional[UserCredentials]:
        """Get user credentials from Google Sheet."""
        try:
            credentials_sheet = self.gc.open(SHEET_NAME).worksheet("Credentials")
            records = credentials_sheet.get_all_records()
            
            for record in records:
                if str(record.get('Telegram ID')) == str(user_id):
                    return UserCredentials(record)
            
            return None
        except Exception as e:
            logger.error(f"Error getting user credentials: {e}")
            return None
    
    def save_to_spreadsheet(self, data: Dict) -> bool:
        """Save data to spreadsheet."""
        try:
            timestamp = format_timestamp()
            no = len(self.sheet.get_all_values())
            
            # Base row data
            row_data = [
                no, timestamp, data['user_id'], data['nama_sa'], data['witel'],
                data['telda'], data.get('sto', ''), data.get('odp', ''), data['cluster'], data['nama_usaha'],
                data['jenis_usaha'], data['pic'], data.get('status_pic', ''), data['hpwa'], data['internet'],
                data['kecepatan'], data['biaya'], data['voc'],
                data.get('location', ''), data.get('file_link', ''),
                data.get('link_gmaps', ''), "Default"
            ]
            
            # Add ODP-related columns if they exist (excluding certain fields)
            excluded_odp_fields = ['odp_latitude', 'odp_longitude', 'odp_avai', 'odp_distance_km']
            odp_columns = []
            for key, value in data.items():
                if (key.startswith('odp_') and
                    key not in ['odp_sto', 'odp_odp'] and  # Avoid duplicates with main fields
                    key not in excluded_odp_fields):  # Exclude specified fields
                    odp_columns.append(value if value is not None else '')
            
            # Append ODP columns to row data
            row_data.extend(odp_columns)
            
            self.sheet.append_row(row_data)
            logger.info(f"Successfully saved data with {len(odp_columns)} additional ODP columns")
            return True
        except Exception as e:
            logger.error(f"Failed to save to spreadsheet: {e}")
            return False
    
    def get_user_records(self, user_id: str) -> List[UserRecord]:
        """Get user's previous records from spreadsheet."""
        try:
            records = self.sheet.get_all_records()
            user_records = []
            
            for record in records:
                if str(record.get('ID')) == str(user_id):
                    user_records.append(UserRecord(record))
            
            return user_records
        except Exception as e:
            logger.error(f"Error getting user records: {e}")
            return []
    
    def get_sheet_data_by_name(self, spreadsheet_name: str, sheet_name: str) -> Optional[List[List]]:
        """Get data from a specific sheet by name."""
        try:
            spreadsheet = self.gc.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
            return data
        except Exception as e:
            logger.error(f"Error getting data from sheet {sheet_name}: {e}")
            return None

# Global instance
sheets_manager = GoogleSheetsManager()

def get_user_credentials(user_id: str) -> Optional[Dict]:
    """Get user credentials from Google Sheet."""
    credentials = sheets_manager.get_user_credentials(user_id)
    return credentials.to_dict() if credentials else None

def save_to_spreadsheet(data: Dict) -> bool:
    """Save data to spreadsheet."""
    return sheets_manager.save_to_spreadsheet(data)

def get_user_records(user_id: str) -> List[Dict]:
    """Get user's previous records from spreadsheet."""
    records = sheets_manager.get_user_records(user_id)
    return [
        {
            'no': record.no,
            'nama_usaha': record.nama_usaha,
            'pic': record.pic,
            'timestamp': record.timestamp
        }
        for record in records
    ]