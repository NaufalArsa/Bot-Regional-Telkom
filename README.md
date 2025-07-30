# Telegram Bot - Modular Structure

This Telegram bot has been refactored into a modular structure for better maintainability, readability, and testability.

## Module Structure

### 1. `config.py`
- **Purpose**: Configuration management and environment variables
- **Contains**: 
  - Environment variable loading and validation
  - Telegram bot configuration (API_ID, API_HASH, BOT_TOKEN)
  - Google Sheets configuration
  - Supabase configuration
  - Channel configuration

### 2. `models.py`
- **Purpose**: Data models and constants
- **Contains**:
  - Column mappings for spreadsheet
  - Option lists for buttons (JENIS_USAHA, INTERNET_OPTIONS, etc.)
  - UserData class for data collection
  - UserCredentials class for user authentication
  - UserRecord class for historical data

### 3. `utils.py`
- **Purpose**: Utility functions and helpers
- **Contains**:
  - Button creation functions
  - Coordinate extraction from Google Maps links
  - Message formatting functions
  - Data validation helpers

### 4. `database.py`
- **Purpose**: Google Sheets integration
- **Contains**:
  - GoogleSheetsManager class
  - User credentials retrieval
  - Data storage to spreadsheet
  - User records retrieval

### 5. `storage.py`
- **Purpose**: File storage operations
- **Contains**:
  - SupabaseStorageManager class
  - File upload to Supabase storage
  - Error handling for storage operations

### 6. `handlers.py`
- **Purpose**: Telegram bot event handlers
- **Contains**:
  - Command handlers (/start, /add, /record)
  - Message handlers for data collection
  - Button callback handlers
  - Location and photo handlers

### 7. `odp_service.py`
- **Purpose**: ODP (Optical Distribution Point) service operations
- **Contains**:
  - ODPService class for ODP location search
  - Distance calculations using geopy
  - ODP data retrieval from Google Sheets
  - Result formatting for display

### 8. `main.py`
- **Purpose**: Main application entry point
- **Contains**:
  - Bot initialization
  - Handler setup
  - Logging configuration
  - Main execution loop

## How to Run

1. **Install dependencies** (same as before):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (same as before):
   - Create a `.env` file with all required variables
   - Ensure `timezone_utils.py` is available

3. **Run the modular bot**:
   ```bash
   python main.py
   ```

## Benefits of Modular Structure

### 1. **Separation of Concerns**
- Each module has a single responsibility
- Configuration is separated from business logic
- Database operations are isolated from bot handlers

### 2. **Improved Maintainability**
- Easy to locate and fix bugs
- Changes in one module don't affect others
- Clear dependencies between modules

### 3. **Better Testability**
- Each module can be tested independently
- Mock objects can be easily created for testing
- Unit tests can focus on specific functionality

### 4. **Enhanced Readability**
- Code is organized logically
- Function and class names are descriptive
- Documentation is module-specific

### 5. **Scalability**
- New features can be added as separate modules
- Existing modules can be extended without affecting others
- Easy to add new handlers or storage backends

## Migration from Original bot.py

The original `bot.py` file contained all functionality in a single file. The modular structure maintains the same functionality while organizing it into logical components:

- **Configuration** → `config.py`
- **Data structures** → `models.py`
- **Helper functions** → `utils.py`
- **Google Sheets operations** → `database.py`
- **File storage** → `storage.py`
- **Bot event handling** → `handlers.py`
- **Main execution** → `main.py`

## New Features

### ODP (Optical Distribution Point) Search
The modular structure now includes ODP search functionality:
- **Command**: `/odp` - Search for nearest ODP locations
- **Input**: Google Maps link or location sharing
- **Output**: 5 nearest ODP locations with distances and availability
- **Data Source**: Google Sheets "ODP" tab

### Automatic STO Detection
The bot now automatically detects STO based on location:
- **Trigger**: When user provides location (Google Maps link or location share) during data collection
- **Process**: Finds nearest ODP and extracts STO information
- **Fallback**: Uses STO from user credentials if detection fails
- **Feedback**: Informs user whether STO was detected automatically

### Usage:
1. **ODP Search**: User sends `/odp` command → Bot requests location → Bot returns 5 nearest ODPs
2. **Data Collection with STO Detection**: User provides location during `/add` process → Bot automatically detects and sets STO → User continues with photo upload

## Dependencies

The modular structure maintains the same external dependencies plus new ones:
- `telethon` - Telegram bot framework
- `gspread` - Google Sheets API
- `supabase` - File storage
- `python-dotenv` - Environment variables
- `oauth2client` - Google authentication
- `requests` - HTTP requests
- `geopy` - Distance calculations for ODP search
- `pandas` - Data processing for ODP operations

## Future Enhancements

With this modular structure, you can easily:
- Add new storage backends (e.g., AWS S3, local storage)
- Implement different database systems (e.g., PostgreSQL, MongoDB)
- Add new bot commands and handlers
- Implement caching mechanisms
- Add comprehensive logging and monitoring
- Create automated tests for each module