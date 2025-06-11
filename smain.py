from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.constants import ParseMode 
import re 
import datetime # لاستخدام الوقت لتحديد متى يتم إرسال رسالة الشكر مرة أخرى

# 1. مفتاح API الخاص بالبوت (احصل عليه من BotFather)
BOT_TOKEN = "7880508466:AAGNAkCwKW_xJb5GEnuD_qUYFJNnbbk7UUk" 

# 2. معرف حسابك الشخصي على تيليجرام (مهم جداً!)
OWNER_TELEGRAM_ID = 7266015804 

# دالة مساعدة للهروب من أحرف Markdown V2 الخاصة
def escape_markdown_v2(text: str) -> str:
    """تفرغ الأحرف الخاصة في نص MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)

# دالة إرسال إخطار للمالك (تم إبقاءها لرسائل الأخطاء فقط)
async def send_owner_notification(context: CallbackContext, message: str):
    try:
        notification_prefix = escape_markdown_v2("🤖 إخطار البوت (للمالك):\n")
        escaped_message = escape_markdown_v2(message)
        final_notification_text = notification_prefix + escaped_message
        
        await context.bot.send_message(chat_id=OWNER_TELEGRAM_ID, text=final_notification_text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        print(f"فشل إرسال إخطار للمالك (جذري): {e}") 

# دالة الترحيب عند بدء المستخدم البوت
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    
    if user_id == OWNER_TELEGRAM_ID:
        await update.message.reply_text(
            "مرحباً بك يا مالك البوت! 👑\n"
            "سأقوم بإعادة توجيه رسائل المستخدمين إليك هنا. للرد عليهم، قم بالرد على الرسالة التي تتضمن معلوماتهم."
        )
    else:
        escaped_first_name = escape_markdown_v2(user_first_name)
        await update.message.reply_text(
            f"مرحباً بك يا {escaped_first_name}!\n"
            "أنا بوت التواصل الخاص بالمطور. يمكنك إرسال رسالتك هنا، وسأقوم بإيصالها له.\n"
            "سيقوم المطور بالرد عليك قريباً عبر هذا البوت."
        )
        # عند البدء، سجل أن رسالة الشكر قد أُرسلت للمستخدم
        context.user_data['last_thank_you_message_sent'] = datetime.datetime.now()

# دالة معالجة جميع الرسائل الواردة
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    
    # إزالة معظم رسائل send_owner_notification لتقليل الضوضاء
    # فقط رسائل الخطأ ستبقى ترسل إخطار للمالك

    # إذا كانت الرسالة من مالك البوت (أنت)
    if user_id == OWNER_TELEGRAM_ID:
        if update.message.reply_to_message:
            replied_to_message_text = update.message.reply_to_message.text 
            replied_to_message_caption = update.message.reply_to_message.caption 

            original_user_id = None
            
            search_text = replied_to_message_text if replied_to_message_text else ""
            if replied_to_message_caption:
                search_text += "\n" + replied_to_message_caption 

            # **التحسين هنا:** تغيير نمط البحث عن User ID
            match = re.search(r"User ID:\s*(\d+)", search_text) 
            if match:
                try:
                    original_user_id = int(match.group(1))
                    # لا يوجد إخطار للمالك هنا إذا تم الاستخراج بنجاح
                except ValueError:
                    await send_owner_notification(context, "خطأ: فشل تحويل User ID المستخرج إلى رقم في رد المالك.")
            
            if not original_user_id and update.message.reply_to_message.entities:
                for entity in update.message.reply_to_message.entities:
                    if entity.type == 'text_link' and hasattr(entity, 'url') and 'user_id:' in entity.url:
                        try:
                            original_user_id = int(entity.url.split('user_id:')[1])
                            # لا يوجد إخطار للمالك هنا
                            break
                        except (ValueError, IndexError):
                            await send_owner_notification(context, "خطأ: فشل استخراج User ID من الرابط المخفي في entities.")
                            pass

            if original_user_id:
                # لا يوجد إخطار للمالك هنا
                try:
                    replied_message_text_escaped = escape_markdown_v2(update.message.text) if update.message.text else "" 
                    replied_message_caption_escaped = escape_markdown_v2(update.message.caption) if update.message.caption else "" 

                    if update.message.photo or update.message.video or update.message.document or \
                       update.message.sticker or update.message.animation or update.message.voice or \
                       update.message.audio or update.message.poll or update.message.dice or \
                       update.message.location or update.message.contact or update.message.game or \
                       update.message.venue or update.message.invoice or update.message.successful_payment or \
                       update.message.story: 
                        
                        await context.bot.copy_message(
                            chat_id=original_user_id,
                            from_chat_id=update.message.chat_id,
                            message_id=update.message.message_id,
                            caption=replied_message_caption_escaped if replied_message_caption_escaped else None, 
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    elif replied_message_text_escaped: 
                        await context.bot.send_message(
                            chat_id=original_user_id,
                            text=replied_message_text_escaped,
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    else: 
                         await update.message.reply_text("لا يوجد محتوى في رسالتك للرد به.")
                         return

                    await update.message.reply_text("تم إرسال ردك إلى المستخدم بنجاح.")
                    # لا يوجد إخطار للمالك هنا
                except Exception as e:
                    await send_owner_notification(context, f"خطأ حرج: فشل إرسال رد المالك للمستخدم الأصلي: {e}")
                    await update.message.reply_text(f"لم أتمكن من إرسال ردك: {e}")
            else:
                await send_owner_notification(context, "خطأ: User ID غير موجود في الرسالة التي تم الرد عليها (تأكد من أن الرسالة تحتوي عليه).")
                await update.message.reply_text(
                    "لا يمكنني تحديد المستخدم الأصلي للرسالة التي رددت عليها.\n"
                    "يرجى التأكد من أنك ترد مباشرةً على رسالة *من مستخدم آخر* التي تتضمن معلوماته."
                )
        else:
            await send_owner_notification(context, "خطأ: رسالة المالك ليست رداً على أي شيء (لذلك لا يمكن تحديد المستخدم الأصلي).")
            await update.message.reply_text(
                "رسالتك هذه ليست رداً على مستخدم.\n"
                "تذكر، للرد على المستخدمين، يجب أن ترد مباشرةً على الرسالة التي تتضمن معلوماتهم."
            )
    # إذا كانت الرسالة من مستخدم عادي (ليس مالك البوت)
    else:
        # لا يوجد إخطار للمالك هنا
        user_message_text_escaped = escape_markdown_v2(update.message.text) if update.message.text else ""
        user_message_caption_escaped = escape_markdown_v2(update.message.caption) if update.message.caption else ""

        escaped_divider = escape_markdown_v2("--- الرسالة الأصلية ---")
        
        user_info_prefix = f"**رسالة جديدة من:** [{escape_markdown_v2(user_first_name)}](tg://user?id={user_id})\n" \
                           f"**User ID:** `{user_id}`\n\n" \
                           f"{escaped_divider}\n"
        
        has_media = update.message.photo or update.message.video or update.message.document or \
                    update.message.sticker or update.message.animation or update.message.voice or \
                    update.message.audio or update.message.poll or update.message.dice or \
                    update.message.location or update.message.contact or update.message.game or \
                    update.message.venue or update.message.invoice or update.message.successful_payment or \
                    update.message.story

        try:
            if has_media:
                final_caption_to_owner = user_info_prefix + user_message_caption_escaped
                await context.bot.copy_message(
                    chat_id=OWNER_TELEGRAM_ID,
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id,
                    caption=final_caption_to_owner, 
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            elif user_message_text_escaped: 
                final_text_to_owner = user_info_prefix + user_message_text_escaped
                await context.bot.send_message(
                    chat_id=OWNER_TELEGRAM_ID,
                    text=final_text_to_owner, 
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                await context.bot.send_message(
                    chat_id=OWNER_TELEGRAM_ID,
                    text=user_info_prefix + "رسالة بدون محتوى نصي أو وسائط مرئية.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            
            # التحكم في رسالة "شكراً لك" للمستخدم
            # يتم إرسالها فقط إذا لم يتم إرسالها خلال آخر 24 ساعة (لتجنب الإزعاج)
            # أو إذا كانت المرة الأولى للمستخدم
            time_since_last_thank_you = (datetime.datetime.now() - context.user_data.get('last_thank_you_message_sent', datetime.datetime.min)).total_seconds()
            
            if time_since_last_thank_you > 24 * 3600 or 'last_thank_you_message_sent' not in context.user_data: # 24 ساعة
                 await update.message.reply_text("شكراً لك! لقد تم إيصال رسالتك إلى المطور وسيتم الرد عليك قريباً.")
                 context.user_data['last_thank_you_message_sent'] = datetime.datetime.now()
            # لا نرسل شيئاً إذا كانت المدة أقل من 24 ساعة

        except Exception as e:
            await send_owner_notification(context, f"خطأ حرج: فشل إرسال رسالة المستخدم (ID: {user_id}) إلى المالك: {e}")
            await update.message.reply_text(f"عذراً، حدث خطأ أثناء إرسال رسالتك: {e}")


# الدالة الرئيسية لتشغيل البوت
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("بوت التواصل يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()