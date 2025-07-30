"""
Data models and constants for the Telegram bot.
Contains data structures, column mappings, and option lists.
"""

from typing import Dict, List

# Column indices for spreadsheet
COLUMNS = {
    'no': 0,
    'timestamp': 1,
    'user_id': 2,
    'nama_sa': 3,
    'witel': 4,
    'telda': 5,
    'sto': 6,
    'odp':7, 
    'cluster': 8,
    'nama_usaha': 9,
    'jenis_usaha': 10,
    'pic': 11,
    'hpwa': 12,
    'internet': 13,
    'kecepatan': 14,
    'biaya': 15,
    'voc': 16,
    'location': 17,
    'file_link': 18,
    'link_gmaps': 19,
    'validitas': 20
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

class UserData:
    """Data structure for user information during data collection."""
    
    def __init__(self, user_id: str, credentials: Dict):
        self.user_id = user_id
        self.nama_sa = credentials['nama_sa']
        self.witel = credentials['witel']
        self.telda = credentials['telda']
        self.cluster = credentials['cluster']
        self.step = 'nama_usaha'
        
        # Data to be collected
        self.sto = None
        self.odp = None
        self.nama_usaha = None
        self.pic = None
        self.status_pic = None
        self.hpwa = None
        self.jenis_usaha = None
        self.internet = None
        self.kecepatan = None
        self.biaya = None
        self.voc = None
        self.location = None
        self.link_gmaps = None
        self.file_link = None
        
        # ODP information
        self.odp_info = None  # Will store complete ODP information as dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for spreadsheet storage."""
        data = {
            'user_id': self.user_id,
            'nama_sa': self.nama_sa,
            'witel': self.witel,
            'telda': self.telda,
            'sto': self.sto,
            'odp': self.odp,
            'cluster': self.cluster,
            'nama_usaha': self.nama_usaha,
            'pic': self.pic,
            'status_pic': self.status_pic,
            'hpwa': self.hpwa,
            'jenis_usaha': self.jenis_usaha,
            'internet': self.internet,
            'kecepatan': self.kecepatan,
            'biaya': self.biaya,
            'voc': self.voc,
            'location': self.location,
            'link_gmaps': self.link_gmaps,
            'file_link': self.file_link
        }
        
        # Add ODP information if available (excluding certain fields)
        if self.odp_info:
            # Fields to exclude from sheet storage
            excluded_fields = ['LATITUDE', 'LONGITUDE', 'AVAI', 'DISTANCE_KM']
            
            for key, value in self.odp_info.items():
                if key not in excluded_fields:
                    # Add ODP fields with prefix to avoid conflicts
                    data[f'odp_{key.lower()}'] = value
        
        return data

class UserCredentials:
    """Data structure for user credentials from Google Sheet."""
    
    def __init__(self, record: Dict):
        self.kode = record.get('Kode SA')
        self.nama_sa = record.get('Nama')
        self.witel = record.get('Witel')
        self.telda = record.get('Telda')
        self.cluster = record.get('Cluster')
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'kode': self.kode,
            'nama_sa': self.nama_sa,
            'witel': self.witel,
            'telda': self.telda,
            'cluster': self.cluster
        }

class UserRecord:
    """Data structure for user's previous records."""
    
    def __init__(self, record: Dict):
        self.no = record.get('No')
        self.nama_usaha = record.get('Nama Usaha')
        self.pic = record.get('PIC')
        self.timestamp = record.get('Timestamp')