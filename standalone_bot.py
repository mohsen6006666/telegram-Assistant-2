#!/usr/bin/env python3
"""
Simplified standalone Telegram bot with no dependencies on other processes
"""

import telebot
import os
import logging
import traceback
import time
import sys
import signal
from typing import Dict, Any, List, Optional

from scraper import WebScraper
from file_handler import FileHandler

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

# User session storage
user_sessions = {}

class TelegramBot:
    def __init__(self):
        self.scraper = WebScraper()
        self.file_handler = FileHandler()
        # Increase timeouts to avoid connection issues
        self.bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=4)
        self._register_handlers()
        logger.info("Bot initialized successfully")
        
    def _register_handlers(self):
        """Register message handlers"""
        # Command handlers
        self.bot.message_handler(commands=['start'])(self.start_command)
        self.bot.message_handler(commands=['help'])(self.help_command)
        self.bot.message_handler(commands=['search'])(self.search_command)
        
        # Regular message handler (for search queries)
        self.bot.message_handler(func=lambda message: True)(self.process_message)
        
        # Callback query handler (for button clicks)
        self.bot.callback_query_handler(func=lambda call: True)(self.handle_callback)
        
        logger.info("Handlers registered successfully")
    
    def start_command(self, message):
        """Handle /start command"""
        user_first_name = message.from_user.first_name
        user_id = message.from_user.id
        logger.info(f"Received /start command from user {user_id} ({user_first_name})")
        
        welcome_message = (
            f"👋 Hello, {user_first_name}!\n\n"
            f"I can help you find movies and send you torrent files directly.\n\n"
            f"To search for movies, use the /search command or simply send me a message with your search term.\n\n"
            f"Example: Avengers\n\n"
            f"You can also specify quality: 720p Avengers\n\n"
            f"I'll send you torrent files that you can upload to webtor.io to stream or download without a torrent client! 🎬\n\n"
            f"Type /help for more information."
        )
        self.bot.send_message(message.chat.id, welcome_message)
    
    def help_command(self, message):
        """Handle /help command"""
        help_text = (
            "🔍 *Search Commands:*\n"
            "/search - Start a search\n"
            "Or directly send your search term\n\n"
            "*Quality Options:*\n"
            "- 720p\n"
            "- 1080p\n"
            "- 2160p (4K)\n\n"
            "*Examples:*\n"
            "• Avengers\n"
            "• 720p Inception\n"
            "• 1080p The Matrix\n\n"
            "*What You'll Get:*\n"
            "I'll send you torrent files that you can upload to webtor.io to stream or download.\n\n"
            "*How to Use the Torrent Files with Webtor.io:*\n"
            "1. Save the torrent file I send you\n"
            "2. Go to webtor.io in your browser\n"
            "3. Click 'Open Torrent' and upload the file I sent you\n"
            "4. Click 'Open' when the file appears\n"
            "5. Wait for it to load (this takes a moment)\n"
            "6. Press the play button to watch directly in your browser or use download options\n"
            "7. No torrent client or additional software needed!"
        )
        self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    
    def search_command(self, message):
        """Handle /search command"""
        self.bot.send_message(
            message.chat.id, 
            "Please enter a movie name to search for:\n\n"
            "Example: Avengers\n\n"
            "You can also specify quality: 720p Avengers"
        )
    
    def process_message(self, message):
        """Process user messages for search"""
        try:
            # Log incoming message
            logger.info(f"Received message from user {message.from_user.id}: {message.text}")
            
            # Ignore commands
            if message.text.startswith('/'):
                return
                
            message_text = message.text.strip()
            
            # Check if the message contains quality specification
            quality_options = ['720p', '1080p', '2160p']
            file_type = None
            
            for quality in quality_options:
                if quality.lower() in message_text.lower():
                    file_type = quality.lower()
                    # Remove the quality from the search query to avoid duplicate results
                    message_text = message_text.lower().replace(quality.lower(), '').strip()
                    break
            
            query = message_text.strip()
            
            if not query:
                self.bot.send_message(
                    message.chat.id,
                    "Please provide a search term.\n"
                    "Example: Avengers\n"
                    "You can also specify quality: 720p Avengers"
                )
                return
            
            # Send searching message
            progress_message = self.bot.send_message(
                message.chat.id,
                f"🔍 Searching for movies with query: '{query}'{' (Quality: ' + file_type + ')' if file_type else ''}...\n"
                "This may take a moment."
            )
            
            # Perform search on YTS.mx API
            results = self.scraper.search_files("yts.mx", query, file_type)
            
            if not results:
                self.bot.edit_message_text(
                    f"❌ No results found for '{query}'.\n\n"
                    f"Try a different search term.",
                    chat_id=message.chat.id,
                    message_id=progress_message.message_id
                )
                return
            
            # Store results in user session
            user_id = message.from_user.id
            user_sessions[user_id] = {
                'search_results': results,
                'query': query,
                'file_type': file_type
            }
            
            # Create results message
            results_text = f"🔍 Found {len(results)} results for '{query}':\n\n"
            
            # Create inline keyboard with results
            from telebot import types
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for i, result in enumerate(results):
                file_type_emoji = "🎬" if result['type'] == 'video' else "📁"
                button_text = f"{i+1}. {file_type_emoji} {result['title'][:30]} ({result['size']})"
                keyboard.add(types.InlineKeyboardButton(button_text, callback_data=f"file_{i}"))
            
            self.bot.edit_message_text(
                results_text, 
                chat_id=message.chat.id,
                message_id=progress_message.message_id,
                reply_markup=keyboard
            )
                
        except Exception as e:
            error_msg = f"Error processing search: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            try:
                self.bot.send_message(
                    message.chat.id,
                    f"❌ Error searching for files.\n\n"
                    f"Please try again later."
                )
            except Exception:
                logger.error("Failed to send error message")
    
    def handle_callback(self, call):
        """Handle callback queries from inline keyboards"""
        user_id = call.from_user.id
        
        # Log callback
        logger.info(f"Received callback from user {user_id}: {call.data}")
        
        # Check the type of callback
        if call.data.startswith("file_"):
            # Movie file selection
            self._handle_file_selection(call, user_id)
        else:
            self.bot.answer_callback_query(call.id, "Unknown callback")
    
    def _handle_file_selection(self, call, user_id: int) -> None:
        """Handle file selection from search results"""
        try:
            # Get the index of the selected file
            file_index = int(call.data.split("_")[1])
            
            # Check if user has an active session
            if user_id not in user_sessions or 'search_results' not in user_sessions[user_id]:
                self.bot.answer_callback_query(call.id, "Search session expired. Please search again.")
                self.bot.edit_message_text(
                    "Search session expired. Please search again.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                return
            
            # Get the selected file
            search_results = user_sessions[user_id]['search_results']
            if file_index >= len(search_results):
                self.bot.answer_callback_query(call.id, "Invalid selection. Please search again.")
                return
            
            selected_file = search_results[file_index]
            
            # Answer the callback to stop loading
            self.bot.answer_callback_query(call.id)
            
            # Update message to show we're preparing the torrent file
            self.bot.edit_message_text(
                f"⏳ Preparing torrent file for: {selected_file['title']}\n"
                f"Quality: {selected_file['quality']}\n"
                f"Size: {selected_file['size']}\n\n"
                f"Please wait, this may take a moment...",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            
            # Download the torrent file directly
            torrent_success, file_path, error_message = self.file_handler.download_file(selected_file['url'])
            
            if not torrent_success:
                self.bot.edit_message_text(
                    f"❌ Failed to download torrent file: {error_message}\n\n"
                    f"Please try another movie or search again.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                return
            
            # Update message to show we're sending the file
            self.bot.edit_message_text(
                f"⏳ Sending torrent file...\n"
                f"Title: {selected_file['title']}\n"
                f"Quality: {selected_file['quality']}\n"
                f"Size: {selected_file['size']}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            
            # Send the torrent file
            chat_id = call.message.chat.id
            caption = (
                f"🎬 Movie: {selected_file['title']}\n"
                f"Quality: {selected_file['quality']}\n\n"
                f"📱 How to watch:\n"
                f"1. Save this torrent file\n"
                f"2. Go to webtor.io in your browser\n"
                f"3. Click 'Open Torrent' and upload this file\n"
                f"4. Click 'Open' and wait for loading\n"
                f"5. Enjoy your movie directly in the browser!"
            )
            
            try:
                # Make sure file_path is not None
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        self.bot.send_document(
                            chat_id=chat_id,
                            document=file,
                            caption=caption
                        )
                else:
                    raise ValueError("Invalid file path")
                
                # Update message to show successful upload
                self.bot.edit_message_text(
                    f"✅ Torrent file sent!\n"
                    f"Title: {selected_file['title']}\n"
                    f"Quality: {selected_file['quality']}\n"
                    f"Size: {selected_file['size']}",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
            except Exception as e:
                logger.error(f"Error sending torrent file: {str(e)}")
                self.bot.edit_message_text(
                    f"❌ Error sending torrent file: {str(e)}\n\n"
                    f"Please try another movie.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
            finally:
                # Clean up the downloaded file
                if file_path:
                    self.file_handler.cleanup_file(file_path)
                    
        except Exception as e:
            error_msg = f"Error processing file selection: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            try:
                self.bot.edit_message_text(
                    f"❌ Error processing your selection.\n\n"
                    f"Please try again later.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
            except Exception:
                logger.error("Failed to send error message")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting bot...")
        
        # Add webhook removal to fix any previously set webhooks
        try:
            self.bot.remove_webhook()
            time.sleep(0.5)  # Small delay to ensure webhook is removed
            logger.info("Webhook removed successfully")
        except Exception as e:
            logger.error(f"Error removing webhook: {str(e)}")
        
        # Handle signals for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal, stopping bot...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the bot with polling - using higher timeouts for reliability
        try:
            logger.info("Starting polling with increased timeouts...")
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Polling error: {str(e)}")
            logger.error(traceback.format_exc())
            # Wait a bit and restart polling
            time.sleep(5)
            logger.info("Restarting polling after error...")
            self.run()


def create_simple_healthcheck():
    """Create a very simple health check file"""
    try:
        with open("healthcheck.html", "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Bot Status</title>
                <meta http-equiv="refresh" content="60">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
                    .status { padding: 20px; background-color: #4CAF50; color: white; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="status">
                    <h2>Bot Status: Running</h2>
                    <p>The Telegram bot is running normally.</p>
                    <p>Last updated: <span id="datetime"></span></p>
                </div>
                <script>
                    document.getElementById("datetime").textContent = new Date().toLocaleString();
                </script>
            </body>
            </html>
            """)
        logger.info("Created health check file")
    except Exception as e:
        logger.error(f"Error creating health check file: {str(e)}")


if __name__ == "__main__":
    try:
        # Kill any existing bot processes first
        os.system("pkill -f 'python.*bot_only.py' || true")
        os.system("pkill -f 'python.*main.py' || true")
        time.sleep(1)  # Give processes time to terminate
        
        # Create health check file
        create_simple_healthcheck()
        
        print("Starting standalone Telegram bot...")
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        logger.critical(traceback.format_exc())