import gspread
import logging
import time
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          filters, CallbackContext)
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram Bot Token
TOKEN = "7755128544:AAES3q1UQZaR83h1-m0H_cejTeps0WN_2lA"

# Google Sheets Configuration
CREDENTIALS_FILE = "cee977be60089a2a104ea9a45ce5282cbd314cbc"

def get_google_sheet_data(sheet_key, sheet_name=None):
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_key(sheet_key)
        if sheet_name:
            worksheet = sheet.worksheet(sheet_name)
        else:
            worksheet = sheet.sheet1
        data = worksheet.get_all_records()
        images = worksheet.col_values(2)  # Assuming images URLs are in the second column
        return data, images
    except Exception as e:
        logging.error(f"Error retrieving data from Google Sheets: {e}")
        return [], []

def capture_screenshot(sheet_url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--hide-scrollbars")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(sheet_url)
        
        # Wait for content to load with explicit wait
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'grid-container')))
        
        # Enhanced styling script with additional cleanup
        modify_view_script = """
        // Remove unnecessary elements including row numbers
        const elementsToHide = [
            '.docs-sheet-container',
            '#docs-chrome',
            '#docs-bars',
            '#docs-header-container',
            '.row-headers-background',
            '.column-headers-background',
            '#docs-side-toolbar',
            '#docs-comment-sidebar',
            '#docs-revisions-sidebar',
            '.row-header-wrapper',
            '.column-header-wrapper',
            '[role="rowheader"]',
            '[role="columnheader"]',
            '.waffle-row-header',
            '.waffle-column-header'
        ];
        
        elementsToHide.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => { 
                if(el) {
                    el.style.display = 'none';
                    el.style.width = '0';
                    el.style.padding = '0';
                    el.style.margin = '0';
                }
            });
        });
        
        // Style the sheet container
        const sheet = document.querySelector('.grid-container');
        if(sheet) {
            // Reset container styles
            sheet.style.position = 'absolute';
            sheet.style.top = '0';
            sheet.style.left = '0';
            sheet.style.backgroundColor = '#ffffff';
            sheet.style.padding = '20px';
            sheet.style.boxSizing = 'border-box';
            sheet.style.borderCollapse = 'collapse';
            sheet.style.maxWidth = '100%';
            sheet.style.margin = '0 auto';
            
            // Enhanced cell styling
            const cells = document.querySelectorAll('.grid-cell');
            cells.forEach(cell => {
                cell.style.padding = '12px 16px';
                cell.style.textAlign = 'center';
                cell.style.borderColor = '#e0e0e0';
                cell.style.borderWidth = '1px';
                cell.style.borderStyle = 'solid';
                cell.style.fontSize = '14px';
                cell.style.fontFamily = 'Arial, sans-serif';
                cell.style.whiteSpace = 'nowrap';
                cell.style.overflow = 'hidden';
                cell.style.textOverflow = 'ellipsis';
            });
            
            // Style header row
            const headerCells = document.querySelectorAll('.grid-cell[data-row-index="0"]');
            headerCells.forEach(cell => {
                cell.style.backgroundColor = '#f8f9fa';
                cell.style.fontWeight = 'bold';
                cell.style.borderBottomWidth = '2px';
                cell.style.borderBottomColor = '#dee2e6';
                cell.style.position = 'sticky';
                cell.style.top = '0';
            });
            
            // Remove any margin/padding from parent elements
            let parent = sheet.parentElement;
            while (parent) {
                parent.style.margin = '0';
                parent.style.padding = '0';
                parent = parent.parentElement;
            }
            
            return {
                width: sheet.offsetWidth + 40,
                height: sheet.offsetHeight + 40
            };
        }
        return null;
        """
        
        # Apply modifications and get dimensions
        dimensions = driver.execute_script(modify_view_script)
        
        if dimensions:
            # Allow time for styles to apply
            time.sleep(3)
            
            # Set viewport and scroll position
            driver.execute_script("window.scrollTo(0, 0);")
            driver.set_window_size(dimensions['width'] + 100, dimensions['height'] + 100)
            
            # Take screenshot with higher quality settings
            screenshot = driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
            
            # Crop and enhance image
            cropped_image = image.crop((56, 50, dimensions['width'], dimensions['height']))
            
            # Improve image quality
            enhanced_image = cropped_image.convert('RGB')
            
            # Save with high quality settings
            screenshot_path = "sheets_screenshot.png"
            enhanced_image.save(
                screenshot_path,
                format='PNG',
                optimize=True,
                quality=95,
                dpi=(300, 300)
            )
            
            logging.info(f"Screenshot captured successfully: {screenshot_path}")
            driver.quit()
            return screenshot_path
            
        else:
            logging.error("Could not locate table element")
            driver.quit()
            return None
            
    except Exception as e:
        logging.error(f"Error capturing screenshot: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

async def handle_google_sheet_link(update: Update, context: CallbackContext):
    user_text = update.message.text.strip()
    parts = user_text.split()
    sheet_url = parts[0]
    sheet_name = parts[1] if len(parts) > 1 else None
    sheet_id = extract_sheet_id(sheet_url)
    if sheet_id:
        data, images = get_google_sheet_data(sheet_id, sheet_name)
        if data:
            report = "📊 Data from Google Sheets:\n\n"
            for record in data[:5]:  # Limit number of records
                report += " - ".join(f"{key}: {value}" for key, value in record.items()) + "\n"
            await update.message.reply_text(report)
            for image_url in images[:5]:  # Limit number of images
                await update.message.reply_photo(photo=image_url)
        else:
            await update.message.reply_text("❌ Unable to retrieve data from Google Sheets.")
    else:
        await update.message.reply_text("Any Help?? \nSend me a valid Google Sheets URL to retrieve data. \n\nuse /gambar and copy the link to capture the table image.")

async def handle_screenshot_request(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("❌ Please include the Google Sheets link after the /gambar command.")
        return
    
    user_text = context.args[0]
    sheet_id = extract_sheet_id(user_text)
    
    if sheet_id:
        await update.message.reply_text("📊 Capturing table... (please wait)")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        screenshot_path = capture_screenshot(sheet_url)
        
        if screenshot_path:
            try:
                with open(screenshot_path, 'rb') as photo:
                    await update.message.reply_photo(photo=photo)
            except Exception as e:
                logging.error(f"Error sending photo: {e}")
                await update.message.reply_text("❌ Failed to send screenshot.")
        else:
            await update.message.reply_text("❌ Failed to capture table image.")
    else:
        await update.message.reply_text("❌ Invalid link or not a Google Sheets URL. \nPlease insert a valid Google Sheets URL.")

def extract_sheet_id(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    if 'spreadsheets' in path_parts and 'd' in path_parts:
        try:
            sheet_id = path_parts[path_parts.index('d') + 1]
            return sheet_id
        except IndexError:
            return None
    return None

async def start(update: Update, context: CallbackContext):
    welcome_message = """
👋 Hello! I'm the PRITI PRQ Daily Report Bot.

🚀 Available commands:
/gambar - Capture sheet image (paste Google Sheet link after command)

Let's get started! 💫
    """
    await update.message.reply_text(welcome_message)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_google_sheet_link))
    app.add_handler(CommandHandler("gambar", handle_screenshot_request))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()