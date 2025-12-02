import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from aiohttp import web

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Health check endpoint
async def health_check(request):
    return web.Response(text="Bot is running! ✅", status=200)

async def home(request):
    return web.Response(text="Telegram Forward Saver Bot is LIVE 🚀", status=200)

# Start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_text = """
🤖 **Forward Saver Bot** 

Mujhe kisi bhi group/channel mein **admin** banao!

✅ **Main kya karunga:**
- Har forwarded message ko us group/channel mein hi save kar dunga
- Original delete ho jaye to mera message rahega
- Permanent backup ban jayega!

📌 **Supported:**
- Photos 📷
- Videos 🎥  
- Documents 📄
- Audio 🎵
- Voice messages 🎤
- Text messages 📝
- Stickers 😊

**Ab mujhe admin banao aur enjoy karo!** 🚀
"""
    await update.message.reply_text(welcome_text)

# Bot handlers
async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwarded messages ko same chat mein save karta hai"""
    
    # Channel post ya message dono handle karo
    message = update.channel_post or update.message
    
    if not message:
        return
    
    # Check if message is forwarded
    if not message.forward_origin:
        return
    
    try:
        chat_id = message.chat.id
        
        # Caption banao - simple backup label
        backup_label = "💾 BACKUP SAVED\n"
        backup_label += f"📅 {message.date.strftime('%d %b %Y, %H:%M')}\n"
        
        original_caption = ""
        if message.caption:
            original_caption = f"\n{message.caption}"
        
        final_caption = backup_label + original_caption
        
        # Different types of media ko same chat mein re-upload karo
        if message.photo:
            photo = message.photo[-1]
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo.file_id,
                caption=final_caption[:1024]
            )
            logger.info(f"✅ Photo backup created in chat {chat_id}")
            
        elif message.video:
            await context.bot.send_video(
                chat_id=chat_id,
                video=message.video.file_id,
                caption=final_caption[:1024]
            )
            logger.info(f"✅ Video backup created in chat {chat_id}")
            
        elif message.document:
            await context.bot.send_document(
                chat_id=chat_id,
                document=message.document.file_id,
                caption=final_caption[:1024]
            )
            logger.info(f"✅ Document backup created in chat {chat_id}")
            
        elif message.audio:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=message.audio.file_id,
                caption=final_caption[:1024]
            )
            logger.info(f"✅ Audio backup created in chat {chat_id}")
            
        elif message.voice:
            await context.bot.send_voice(
                chat_id=chat_id,
                voice=message.voice.file_id,
                caption=final_caption[:1024]
            )
            logger.info(f"✅ Voice backup created in chat {chat_id}")
            
        elif message.video_note:
            await context.bot.send_video_note(
                chat_id=chat_id,
                video_note=message.video_note.file_id
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=backup_label
            )
            logger.info(f"✅ Video note backup created in chat {chat_id}")
            
        elif message.sticker:
            await context.bot.send_sticker(
                chat_id=chat_id,
                sticker=message.sticker.file_id
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=backup_label
            )
            logger.info(f"✅ Sticker backup created in chat {chat_id}")
            
        elif message.text:
            text_content = f"{backup_label}\n💬 Message:\n{message.text}"
            await context.bot.send_message(
                chat_id=chat_id,
                text=text_content[:4096]
            )
            logger.info(f"✅ Text backup created in chat {chat_id}")
            
    except Exception as e:
        logger.error(f"❌ Error creating backup: {e}")

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
    
    logger.info(f"🌐 Web server started on port {port}")

async def main():
    """Bot ko start karo"""
    
    TOKEN = os.environ.get('BOT_TOKEN')
    
    if not TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    # Application banao
    application = Application.builder().token(TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start_command))
    
    # Forwarded messages handler - dono message aur channel_post ke liye
    application.add_handler(
        MessageHandler(
            filters.FORWARDED & ~filters.COMMAND,
            handle_forwarded_message
        )
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Web server
    await start_web_server()
    
    logger.info("🚀 Bot started!")
    logger.info("📡 Polling mode active...")
    logger.info("💾 Bot will save backups in same chat!")
    
    # Start bot
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        # Keep running
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
