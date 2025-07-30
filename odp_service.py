"""
ODP (Optical Distribution Point) service module.
Handles ODP location search and distance calculations.
"""

import logging
import pandas as pd
from typing import Optional, List, Dict
from geopy.distance import geodesic
from database import sheets_manager
from config import SHEET_NAME

logger = logging.getLogger(__name__)

class ODPService:
    """Service for ODP-related operations."""
    
    def __init__(self):
        self.spreadsheet_name = SHEET_NAME
    
    def get_odp_dataframe(self) -> Optional[pd.DataFrame]:
        """Get ODP data from Google Sheets tab 'ODP'."""
        try:
            data = sheets_manager.get_sheet_data_by_name(self.spreadsheet_name, "ODP")
            if data and len(data) > 1:
                headers = data[0]
                rows = data[1:]
                df = pd.DataFrame(rows, columns=headers)
                logger.info(f"Successfully loaded {len(df)} rows from sheet: ODP")
                return df
            else:
                logger.warning("No data found in sheet: ODP")
                return None
        except Exception as e:
            logger.error(f"Error getting data from sheet ODP: {e}")
            return None
    
    def find_nearest_odp(self, user_lat: float, user_lon: float, limit: int = 5) -> Optional[pd.DataFrame]:
        """Find nearest ODP locations to user coordinates."""
        df = self.get_odp_dataframe()
        if df is None:
            return None
        
        if not all(col in df.columns for col in ["STO", "ODP", "LATITUDE", "LONGITUDE"]):
            logger.error("ODP data missing required columns")
            return None
        
        try:
            user_location = (user_lat, user_lon)
            
            # Ensure AVAI column exists
            columns_needed = ["STO", "ODP", "LATITUDE", "LONGITUDE"]
            if "AVAI" in df.columns:
                columns_needed.append("AVAI")
            else:
                df["AVAI"] = "N/A"
                columns_needed.append("AVAI")
            
            # Filter out rows with missing data
            locations = df[columns_needed].dropna(subset=["STO", "ODP", "LATITUDE", "LONGITUDE"])
            
            # Convert lat/lon to float for distance calculation
            locations["LATITUDE"] = locations["LATITUDE"].astype(float)
            locations["LONGITUDE"] = locations["LONGITUDE"].astype(float)
            
            # Calculate distances
            locations["DISTANCE_KM"] = locations.apply(
                lambda row: geodesic(user_location, (row["LATITUDE"], row["LONGITUDE"])).km,
                axis=1
            )
            
            # Return nearest locations
            nearest = locations.sort_values(by="DISTANCE_KM").head(limit)
            return nearest
            
        except Exception as e:
            logger.error(f"Error calculating ODP distances: {e}")
            return None
    
    def format_odp_results(self, nearest_odp: pd.DataFrame) -> str:
        """Format ODP results for display."""
        if nearest_odp is None or nearest_odp.empty:
            return "❌ Tidak ada data ODP yang ditemukan."
        
        msg = "\n=== 5 ODP Terdekat ===\n"
        for i, row in enumerate(nearest_odp.itertuples(index=False), 1):
            sto = getattr(row, 'STO', 'N/A')
            odp = getattr(row, 'ODP', '-')
            lat = getattr(row, 'LATITUDE', 0.0)
            lon = getattr(row, 'LONGITUDE', 0.0)
            dist = getattr(row, 'DISTANCE_KM', 0.0)
            avai = getattr(row, 'AVAI', 'N/A')
            
            try:
                lat_float = float(str(lat)) if lat else 0.0
                lon_float = float(str(lon)) if lon else 0.0
            except (ValueError, TypeError):
                lat_float = 0.0
                lon_float = 0.0
            
            dist_meter = dist * 1000
            odp_maps = f"https://www.google.com/maps?q={lat_float},{lon_float}"
            
            msg += (
                f"{i}. {odp} | {lat_float:.6f},{lon_float:.6f} | {dist_meter:.2f} m | "
                f"Port Tersedia: {avai} | [Lihat di Maps]({odp_maps})\n"
            )
        
        return msg
    
    def get_complete_odp_info(self, user_lat: float, user_lon: float) -> Optional[Dict]:
        """Get complete ODP information from the nearest ODP location."""
        nearest_odp = self.find_nearest_odp(user_lat, user_lon, limit=1)
        if nearest_odp is None or nearest_odp.empty:
            return None
        
        try:
            # Get the first (nearest) ODP
            first_row = nearest_odp.iloc[0]
            
            # Create a dictionary with all available ODP information
            odp_info = {}
            for column in nearest_odp.columns:
                value = first_row[column]
                # Convert to string and handle empty values
                odp_info[column] = str(value) if pd.notna(value) and value != '' else None
            
            logger.info(f"Found complete ODP info: {odp_info}")
            return odp_info
                
        except Exception as e:
            logger.error(f"Error getting complete ODP info: {e}")
            return None
    
    def get_sto_from_nearest_odp(self, user_lat: float, user_lon: float) -> Optional[str]:
        """Get STO from the nearest ODP location."""
        odp_info = self.get_complete_odp_info(user_lat, user_lon)
        if odp_info and "STO" in odp_info:
            return odp_info["STO"]
        return None
    
    def format_odp_info_for_user(self, odp_info: Dict) -> str:
        """Format ODP information for user display."""
        if not odp_info:
            return "❌ Informasi ODP tidak tersedia."
        
        msg = "📍 **Informasi ODP Terdekat:**\n\n"
        
        # Priority fields to show first
        priority_fields = ["STO", "ODP", "LATITUDE", "LONGITUDE", "DISTANCE_KM", "AVAI"]
        
        # Show priority fields first
        for field in priority_fields:
            if field in odp_info and odp_info[field] is not None:
                if field == "DISTANCE_KM":
                    try:
                        distance_m = float(odp_info[field]) * 1000
                        msg += f"🔹 **Jarak:** {distance_m:.2f} meter\n"
                    except (ValueError, TypeError):
                        msg += f"🔹 **{field}:** {odp_info[field]}\n"
                elif field == "AVAI":
                    msg += f"🔹 **Port Tersedia:** {odp_info[field]}\n"
                elif field in ["LATITUDE", "LONGITUDE"]:
                    try:
                        coord = float(odp_info[field])
                        msg += f"🔹 **{field}:** {coord:.6f}\n"
                    except (ValueError, TypeError):
                        msg += f"🔹 **{field}:** {odp_info[field]}\n"
                else:
                    msg += f"🔹 **{field}:** {odp_info[field]}\n"
        
        # Show other fields
        for field, value in odp_info.items():
            if field not in priority_fields and value is not None:
                msg += f"🔹 **{field}:** {value}\n"
        
        return msg

# Global instance
odp_service = ODPService()