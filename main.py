import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for health check (UptimeRobot ke liye)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! ✅", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Bot handlers
async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwarded messages ko handle karta hai aur unhe bot ke saved messages mein store karta hai"""
    
    message = update.message
    
    # Check if message is forwarded
    if not message.forward_origin:
        return
    
    try:
        # Message details
        chat_name = update.effective_chat.title or "Private Chat"
        user_name = update.effective_user.first_name
        
        # Caption banao with original source info
        caption_text = f"📩 Forwarded from: {chat_name}\n"
        caption_text += f"👤 Saved by: {user_name}\n"
        caption_text += f"🔗 Chat ID: {update.effective_chat.id}\n"
        
        if message.caption:
            caption_text += f"\n📝 Original Caption:\n{message.caption}"
        
        # Different types of media ko handle karo
        if message.photo:
            # Highest quality photo lelo
            photo = message.photo[-1]
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=photo.file_id,
                caption=caption_text[:1024]  # Telegram limit
            )
            logger.info(f"Photo saved from {chat_name}")
            
        elif message.video:
            await context.bot.send_video(
                chat_id=update.effective_user.id,
                video=message.video.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"Video saved from {chat_name}")
            
        elif message.document:
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                document=message.document.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"Document saved from {chat_name}")
            
        elif message.audio:
            await context.bot.send_audio(
                chat_id=update.effective_user.id,
                audio=message.audio.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"Audio saved from {chat_name}")
            
        elif message.voice:
            await context.bot.send_voice(
                chat_id=update.effective_user.id,
                voice=message.voice.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"Voice message saved from {chat_name}")
            
        elif message.video_note:
            await context.bot.send_video_note(
                chat_id=update.effective_user.id,
                video_note=message.video_note.file_id
            )
            # Video notes don't support captions, so send text separately
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=caption_text
            )
            logger.info(f"Video note saved from {chat_name}")
            
        elif message.text:
            # Text messages ko bhi save karo
            text_content = f"{caption_text}\n\n💬 Message:\n{message.text}"
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text_content[:4096]  # Telegram text limit
            )
            logger.info(f"Text message saved from {chat_name}")
            
    except Exception as e:
        logger.error(f"Error handling forwarded message: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Bot ko start karo"""
    
    # Bot token environment variable se lo
    TOKEN = os.environ.get('BOT_TOKEN')
    
    if not TOKEN:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        return
    
    # Application banao
    application = Application.builder().token(TOKEN).build()
    
    # Handler add karo - sirf forwarded messages ke liye
    application.add_handler(
        MessageHandler(
            filters.FORWARDED & ~filters.COMMAND,
            handle_forwarded_message
        )
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Flask server ko alag thread mein chalao
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    logger.info("🚀 Bot started successfully!")
    logger.info("📡 Webhook mode - waiting for updates...")
    
    # Bot ko polling mode mein chalao
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
