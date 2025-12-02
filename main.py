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
- Har forwarded message ko automatically save karunga
- Tumhare personal chat mein bhej dunga
- Original delete ho jaye to bhi tumhare paas rahega!

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
    """Forwarded messages ko handle karta hai"""
    
    # Channel post ya message dono handle karo
    message = update.channel_post or update.message
    
    if not message:
        return
    
    # Check if message is forwarded
    if not message.forward_origin:
        return
    
    try:
        # Bot owner ka user ID - pehle message se automatically detect hoga
        # Ya tum manually set kar sakte ho
        target_user_id = update.effective_user.id if update.effective_user else None
        
        # Agar channel post hai to owner ko directly bhejenge
        if update.channel_post:
            # Channel posts ke liye owner ID manually set karo
            # Ya first group message se detect karo
            if not hasattr(context.bot_data, 'owner_id'):
                logger.warning("⚠️ Owner ID not set. Skipping channel post.")
                return
            target_user_id = context.bot_data.get('owner_id')
        
        if not target_user_id:
            # Agar user ID nahi mili to skip karo
            return
        
        # Message details
        chat_name = message.chat.title or "Private Chat"
        user_name = message.sender_chat.title if message.sender_chat else "Unknown"
        
        # Caption banao with original source info
        caption_text = f"📩 From: {chat_name}\n"
        caption_text += f"👤 By: {user_name}\n"
        caption_text += f"🔗 Chat ID: {message.chat.id}\n"
        caption_text += f"📅 {message.date.strftime('%d %b %Y, %H:%M')}\n"
        
        if message.caption:
            caption_text += f"\n📝 Caption:\n{message.caption[:800]}"  # Limit caption
        
        # Different types of media ko handle karo
        if message.photo:
            photo = message.photo[-1]
            await context.bot.send_photo(
                chat_id=target_user_id,
                photo=photo.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"✅ Photo saved from {chat_name}")
            
        elif message.video:
            await context.bot.send_video(
                chat_id=target_user_id,
                video=message.video.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"✅ Video saved from {chat_name}")
            
        elif message.document:
            await context.bot.send_document(
                chat_id=target_user_id,
                document=message.document.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"✅ Document saved from {chat_name}")
            
        elif message.audio:
            await context.bot.send_audio(
                chat_id=target_user_id,
                audio=message.audio.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"✅ Audio saved from {chat_name}")
            
        elif message.voice:
            await context.bot.send_voice(
                chat_id=target_user_id,
                voice=message.voice.file_id,
                caption=caption_text[:1024]
            )
            logger.info(f"✅ Voice saved from {chat_name}")
            
        elif message.video_note:
            await context.bot.send_video_note(
                chat_id=target_user_id,
                video_note=message.video_note.file_id
            )
            await context.bot.send_message(
                chat_id=target_user_id,
                text=caption_text
            )
            logger.info(f"✅ Video note saved from {chat_name}")
            
        elif message.sticker:
            await context.bot.send_sticker(
                chat_id=target_user_id,
                sticker=message.sticker.file_id
            )
            await context.bot.send_message(
                chat_id=target_user_id,
                text=caption_text
            )
            logger.info(f"✅ Sticker saved from {chat_name}")
            
        elif message.text:
            text_content = f"{caption_text}\n\n💬 Message:\n{message.text}"
            await context.bot.send_message(
                chat_id=target_user_id,
                text=text_content[:4096]
            )
            logger.info(f"✅ Text saved from {chat_name}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def set_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner ID set karne ke liye - bot ko private chat mein /setowner bhejo"""
    if update.effective_user:
        context.bot_data['owner_id'] = update.effective_user.id
        await update.message.reply_text(
            f"✅ Owner set: {update.effective_user.first_name}\n"
            f"ID: {update.effective_user.id}\n\n"
            f"Ab main tumhe sab forwarded messages bhejunga! 🚀"
        )
        logger.info(f"✅ Owner set: {update.effective_user.id}")

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
    application.add_handler(CommandHandler("setowner", set_owner))
    
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
    logger.info("⚠️ First send /setowner to bot in private chat!")
    
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
