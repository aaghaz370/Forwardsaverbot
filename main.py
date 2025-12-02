import os
import logging
import asyncio
import re
from telegram import Update, InputMediaVideo, InputMediaPhoto, InputMediaDocument, InputMediaAudio
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from aiohttp import web

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# 🎯 CONFIGURATION - YE SETTINGS CHANGE KARO
# ============================================

# Caption mein se remove karne ke liye text (list mein daalo)
REMOVE_TEXT = [
    "✨Buy Premium",
    "Click here to Buy",
    "🎖All Branches",
    "⚡️Study Ratna⚡️",
    "〰️〰️〰️〰️〰️〰️〰️〰️",
]

# Caption mein replace karne ke liye (old_text: new_text)
REPLACE_TEXT = {
    # Example: "OLD TEXT": "NEW TEXT"
    # "VootKids": "Netflix",
}

# Naya caption add karna hai? (agar empty string "" ho to kuch add nahi hoga)
ADD_CAPTION = ""
# Example: ADD_CAPTION = "\n\n📢 Join: @YourChannel"

# Thumbnail change karna hai? (file_id daalo, ya "" chhod do)
CUSTOM_THUMBNAIL = ""
# Thumbnail kaise milega: kisi video ka thumbnail manually set karo, uska file_id copy karo

# Caption completely remove karna hai? (True ya False)
REMOVE_CAPTION_COMPLETELY = False

# Backup label show karna hai? (True = show, False = hide)
SHOW_BACKUP_LABEL = False

# ============================================

# Health check endpoint
async def health_check(request):
    return web.Response(text="Bot is running! ✅", status=200)

async def home(request):
    return web.Response(text="Telegram Forward Saver Bot is LIVE 🚀", status=200)

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_text = """
🤖 **Forward Saver Bot** 

✅ **Features:**
- Forwarded messages ko same chat mein save karta hai
- Original delete ho jaye to backup rahega
- Caption ko customize kar sakta hai
- Thumbnail change kar sakta hai
- Auto-filter unwanted text

**Mujhe admin banao aur enjoy karo!** 🚀
"""
    await update.message.reply_text(welcome_text)

def clean_caption(caption):
    """Caption ko clean karta hai based on settings"""
    
    if not caption:
        return ""
    
    # Agar completely remove karna hai
    if REMOVE_CAPTION_COMPLETELY:
        return ""
    
    cleaned = caption
    
    # Remove specific text
    for text in REMOVE_TEXT:
        cleaned = cleaned.replace(text, "")
    
    # Replace text
    for old_text, new_text in REPLACE_TEXT.items():
        cleaned = cleaned.replace(old_text, new_text)
    
    # Extra spaces aur newlines clean karo
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Multiple newlines
    cleaned = cleaned.strip()
    
    # Naya text add karo
    if ADD_CAPTION:
        cleaned += ADD_CAPTION
    
    return cleaned

async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwarded messages ko same chat mein save karta hai with customization"""
    
    message = update.channel_post or update.message
    
    if not message:
        return
    
    if not message.forward_origin:
        return
    
    try:
        chat_id = message.chat.id
        
        # Original caption ko clean karo
        original_caption = message.caption or ""
        cleaned_caption = clean_caption(original_caption)
        
        # Backup label (optional)
        backup_label = ""
        if SHOW_BACKUP_LABEL:
            backup_label = f"💾 BACKUP SAVED\n📅 {message.date.strftime('%d %b %Y, %H:%M')}\n\n"
        
        final_caption = backup_label + cleaned_caption
        
        # Thumbnail (agar set hai to)
        thumbnail = CUSTOM_THUMBNAIL if CUSTOM_THUMBNAIL else None
        
        # Different media types handle karo
        if message.photo:
            photo = message.photo[-1]
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo.file_id,
                caption=final_caption[:1024] if final_caption else None
            )
            logger.info(f"✅ Photo backup: {chat_id}")
            
        elif message.video:
            # Video ke liye thumbnail customize kar sakte ho
            send_kwargs = {
                'chat_id': chat_id,
                'video': message.video.file_id,
                'caption': final_caption[:1024] if final_caption else None,
            }
            
            # Custom thumbnail add karo (agar available hai)
            if thumbnail:
                send_kwargs['thumbnail'] = thumbnail
            
            await context.bot.send_video(**send_kwargs)
            logger.info(f"✅ Video backup: {chat_id}")
            
        elif message.document:
            send_kwargs = {
                'chat_id': chat_id,
                'document': message.document.file_id,
                'caption': final_caption[:1024] if final_caption else None,
            }
            
            if thumbnail:
                send_kwargs['thumbnail'] = thumbnail
            
            await context.bot.send_document(**send_kwargs)
            logger.info(f"✅ Document backup: {chat_id}")
            
        elif message.audio:
            send_kwargs = {
                'chat_id': chat_id,
                'audio': message.audio.file_id,
                'caption': final_caption[:1024] if final_caption else None,
            }
            
            if thumbnail:
                send_kwargs['thumbnail'] = thumbnail
            
            await context.bot.send_audio(**send_kwargs)
            logger.info(f"✅ Audio backup: {chat_id}")
            
        elif message.voice:
            await context.bot.send_voice(
                chat_id=chat_id,
                voice=message.voice.file_id,
                caption=final_caption[:1024] if final_caption else None
            )
            logger.info(f"✅ Voice backup: {chat_id}")
            
        elif message.video_note:
            await context.bot.send_video_note(
                chat_id=chat_id,
                video_note=message.video_note.file_id
            )
            if final_caption:
                await context.bot.send_message(chat_id=chat_id, text=final_caption[:4096])
            logger.info(f"✅ Video note backup: {chat_id}")
            
        elif message.sticker:
            await context.bot.send_sticker(
                chat_id=chat_id,
                sticker=message.sticker.file_id
            )
            if final_caption:
                await context.bot.send_message(chat_id=chat_id, text=final_caption[:4096])
            logger.info(f"✅ Sticker backup: {chat_id}")
            
        elif message.text:
            text_content = clean_caption(message.text)
            if SHOW_BACKUP_LABEL:
                text_content = backup_label + text_content
            await context.bot.send_message(
                chat_id=chat_id,
                text=text_content[:4096] if text_content else "💾 Backup saved"
            )
            logger.info(f"✅ Text backup: {chat_id}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Error: {context.error}")

async def start_web_server():
    """Web server for health checks"""
    app = web.Application()
    app.router.add_get('/', home)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Web server: {port}")

async def main():
    """Bot start"""
    
    TOKEN = os.environ.get('BOT_TOKEN')
    
    if not TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(
            filters.FORWARDED & ~filters.COMMAND,
            handle_forwarded_message
        )
    )
    application.add_error_handler(error_handler)
    
    # Web server
    await start_web_server()
    
    logger.info("🚀 Bot started!")
    logger.info("💾 Saving backups in same chat")
    
    # Start polling
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Stopping...")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
