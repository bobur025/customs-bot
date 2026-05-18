import os
import random
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    filters, ContextTypes, CallbackQueryHandler
)
import pandas as pd
from database import Database

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Состояния диалога ───────────────────────────────────────────────────────
(
    FULL_NAME,
    REGION,
    POST,
    DOCUMENT,
    TEST_COUNT,
    TESTING,
    AFTER_TEST,
) = range(7)

# ─── Данные ──────────────────────────────────────────────────────────────────
REGIONS_POSTS = {
    "Тошкент шаҳри": ["Тошкент халқаро аэропорти", "Тошкент темир йўл", "Чиланзор пости"],
    "Тошкент вилояти": ["Оккупюк БПП", "Келес БПП", "Охунбобоев БПП"],
    "Самарқанд вилояти": ["Самарқанд БПП", "Самарқанд аэропорти", "Каттақўрғон пости"],
    "Бухоро вилояти": ["Бухоро БПП", "Қоровулбозор БПП", "Олот БПП"],
    "Қашқадарё вилояти": ["Қарши БПП", "Бешкент пости", "Ғузор пости"],
    "Сурхондарё вилояти": ["Термиз БПП", "Термиз аэропорти", "Айритом БПП"],
    "Навоий вилояти": ["Навоий аэропорти", "Учқудуқ пости", "Зарафшон пости"],
    "Жиззах вилояти": ["Достлик БПП", "Жиззах пости"],
    "Сирдарё вилояти": ["Сирдарё пости", "Гулистон пости"],
    "Фарғона вилояти": ["Фарғона аэропорти", "Андижон аэропорти", "Қўқон пости"],
    "Андижон вилояти": ["Андижон БПП", "Хонобод БПП"],
    "Наманган вилояти": ["Наманган аэропорти", "Наманган БПП"],
    "Хоразм вилояти": ["Урганч аэропорти", "Хонқа пости"],
    "Қорақалпоғистон Республикаси": ["Нукус аэропорти", "Тахиаташ пости", "Қўнғирот пости"],
}

db = Database()
df_all = pd.read_excel("tests.xlsx").dropna(subset=["question"])
DOCUMENTS = sorted(df_all["document"].dropna().unique().tolist())

# ─── Вспомогательные функции ─────────────────────────────────────────────────
def main_menu_keyboard():
    return ReplyKeyboardMarkup([["🏠 Бош меню"]], resize_keyboard=True)

def back_keyboard():
    return ReplyKeyboardMarkup([["⬅️ Орқага"]], resize_keyboard=True)

def back_and_home_keyboard():
    return ReplyKeyboardMarkup([["⬅️ Орқага", "🏠 Бош меню"]], resize_keyboard=True)

# ─── /start ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Хуш келибсиз!\n\n"
        "Бу бот божхона ходимлари учун тест синови тизими.\n\n"
        "Илтимос, тўлиқ исмингизни (Фамилия Исм Отасининг исми) киритинг:",
        reply_markup=ReplyKeyboardRemove()
    )
    return FULL_NAME

async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name.split()) < 2:
        await update.message.reply_text("❗ Илтимос, тўлиқ ФИО киритинг (Фамилия Исм Отасининг исми):")
        return FULL_NAME
    context.user_data["full_name"] = name
    regions = list(REGIONS_POSTS.keys())
    keyboard = [[r] for r in regions] + [["⬅️ Орқага"]]
    await update.message.reply_text(
        f"✅ Раҳмат, {name}!\n\nИлтимос, вилоятингизни танланг:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return REGION

async def handle_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "⬅️ Орқага":
        await update.message.reply_text("Исмингизни қайта киритинг:", reply_markup=ReplyKeyboardRemove())
        return FULL_NAME
    if text not in REGIONS_POSTS:
        await update.message.reply_text("❗ Рўйхатдан вилоятни танланг:")
        return REGION
    context.user_data["region"] = text
    posts = REGIONS_POSTS[text]
    keyboard = [[p] for p in posts] + [["⬅️ Орқага"]]
    await update.message.reply_text(
        f"📍 {text}\n\nБожхона постини танланг:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return POST

async def handle_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "⬅️ Орқага":
        regions = list(REGIONS_POSTS.keys())
        keyboard = [[r] for r in regions] + [["⬅️ Орқага"]]
        await update.message.reply_text("Вилоятни танланг:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return REGION
    region = context.user_data.get("region", "")
    if text not in REGIONS_POSTS.get(region, []):
        await update.message.reply_text("❗ Рўйхатдан постни танланг:")
        return POST
    context.user_data["post"] = text
    keyboard = [[d] for d in DOCUMENTS] + [["⬅️ Орқага"]]
    await update.message.reply_text(
        "📄 Норматив ҳужжатни танланг:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return DOCUMENT

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "⬅️ Орқага":
        region = context.user_data.get("region", "")
        posts = REGIONS_POSTS.get(region, [])
        keyboard = [[p] for p in posts] + [["⬅️ Орқага"]]
        await update.message.reply_text("Постни танланг:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return POST
    if text not in DOCUMENTS:
        await update.message.reply_text("❗ Рўйхатдан ҳужжатни танланг:")
        return DOCUMENT
    context.user_data["document"] = text
    doc_questions = df_all[df_all["document"] == text]
    total = len(doc_questions)
    context.user_data["total_available"] = total

    if total < 20:
        context.user_data["test_count"] = total
        await update.message.reply_text(
            f"📋 «{text}» бўйича жами {total} та савол мавжуд.\n"
            f"Барча {total} та савол берилади.\n\nТайёрмисиз? Тест бошланяпти...",
            reply_markup=ReplyKeyboardRemove()
        )
        await start_test(update, context)
        return TESTING

    options = [20, 30, 40, 50]
    available = [o for o in options if o <= total]
    keyboard = [[str(o) for o in available]] + [["⬅️ Орқага"]]
    await update.message.reply_text(
        f"📋 «{text}» бўйича {total} та савол мавжуд.\n\nНечта савол ечмоқчисиз?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return TEST_COUNT

async def handle_test_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "⬅️ Орқага":
        keyboard = [[d] for d in DOCUMENTS] + [["⬅️ Орқага"]]
        await update.message.reply_text("Норматив ҳужжатни танланг:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return DOCUMENT
    try:
        count = int(text)
    except ValueError:
        await update.message.reply_text("❗ Рақам танланг:")
        return TEST_COUNT
    total = context.user_data.get("total_available", 0)
    if count not in [20, 30, 40, 50] or count > total:
        await update.message.reply_text("❗ Рўйхатдан танланг:")
        return TEST_COUNT
    context.user_data["test_count"] = count
    await update.message.reply_text(
        f"✅ {count} та савол танланди.\n\nТайёрмисиз? Тест бошланяпти...",
        reply_markup=ReplyKeyboardRemove()
    )
    await start_test(update, context)
    return TESTING

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = context.user_data["document"]
    count = context.user_data["test_count"]
    doc_questions = df_all[df_all["document"] == doc].copy()
    selected = doc_questions.sample(n=min(count, len(doc_questions))).to_dict("records")
    context.user_data["questions"] = selected
    context.user_data["current_q"] = 0
    context.user_data["correct"] = 0
    context.user_data["wrong"] = 0
    context.user_data["start_time"] = datetime.now().isoformat()
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = context.user_data["questions"]
    idx = context.user_data["current_q"]
    total = len(questions)
    q = questions[idx]
    options = [
        str(q.get("option_1", "")).strip(),
        str(q.get("option_2", "")).strip(),
        str(q.get("option_3", "")).strip(),
        str(q.get("option_4", "")).strip(),
    ]
    options = [o for o in options if o and o != "nan"]
    context.user_data["current_options"] = options
    context.user_data["correct_answer"] = str(q.get("correct_answer", "")).strip()
    keyboard = [[o] for o in options]
    text = (
        f"📝 Савол {idx+1}/{total}\n\n"
        f"{q['question']}"
    )
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") == "after_test":
        return await handle_after_test_menu(update, context)

    text = update.message.text.strip()
    questions = context.user_data.get("questions", [])
    idx = context.user_data.get("current_q", 0)
    correct_answer = context.user_data.get("correct_answer", "")
    options = context.user_data.get("current_options", [])

    if text not in options:
        await update.message.reply_text("❗ Илтимос, берилган вариантлардан бирини танланг:")
        return TESTING

    if text == correct_answer:
        context.user_data["correct"] += 1
    else:
        context.user_data["wrong"] += 1

    context.user_data["current_q"] += 1
    next_idx = context.user_data["current_q"]

    if next_idx >= len(questions):
        await finish_test(update, context)
        return AFTER_TEST

    await send_question(update, context)
    return TESTING

async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    correct = context.user_data["correct"]
    wrong = context.user_data["wrong"]
    total = len(context.user_data["questions"])
    percent = round((correct / total) * 100, 1) if total > 0 else 0

    if percent >= 90:
        grade = "⭐⭐⭐ А'ло"
    elif percent >= 70:
        grade = "⭐⭐ Яхши"
    elif percent >= 50:
        grade = "⭐ Қониқарли"
    else:
        grade = "❌ Қониқarsiz"

    result_text = (
        f"🏁 Тест якунланди!\n\n"
        f"👤 {context.user_data['full_name']}\n"
        f"📍 {context.user_data['region']} — {context.user_data['post']}\n"
        f"📄 {context.user_data['document']}\n\n"
        f"✅ Тўғри жавоблар: {correct}\n"
        f"❌ Нотўғри жавоблар: {wrong}\n"
        f"📊 Фоиз: {percent}%\n"
        f"🎯 Баҳо: {grade}"
    )

    db.save_result(
        user_id=update.effective_user.id,
        username=update.effective_user.username or "",
        full_name=context.user_data["full_name"],
        region=context.user_data["region"],
        post=context.user_data["post"],
        document=context.user_data["document"],
        total=total,
        correct=correct,
        wrong=wrong,
        percent=percent,
        start_time=context.user_data.get("start_time", ""),
        end_time=datetime.now().isoformat()
    )

    keyboard = ReplyKeyboardMarkup(
        [["🔁 Қайта ечиш", "🏠 Бош меню"]],
        resize_keyboard=True
    )
    context.user_data["state"] = "after_test"
    await update.message.reply_text(result_text, reply_markup=keyboard)

async def handle_after_test_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "🔁 Қайта ечиш":
        context.user_data["state"] = None
        total = context.user_data.get("total_available", 0)
        count = context.user_data.get("test_count", 0)
        doc = context.user_data.get("document", "")
        await update.message.reply_text(
            f"🔁 «{doc}» бўйича {count} та савол билан қайта бошланяпти...",
            reply_markup=ReplyKeyboardRemove()
        )
        await start_test(update, context)
        return TESTING
    elif text == "🏠 Бош меню":
        context.user_data.clear()
        await update.message.reply_text(
            "🏠 Бош менюга қайтдингиз.\n\nЯнги тест бошлаш учун /start ни босинг.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        keyboard = ReplyKeyboardMarkup([["🔁 Қайта ечиш", "🏠 Бош меню"]], resize_keyboard=True)
        await update.message.reply_text("Илтимос, қуйидагилардан бирини танланг:", reply_markup=keyboard)
        return AFTER_TEST

async def home_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🏠 Бош менюга қайтдингиз.\n\nЯнги тест бошлаш учун /start ни босинг.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ─── Админ команды ────────────────────────────────────────────────────────────
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Сиз администратор эмассиз.")
        return
    results = db.get_all_results()
    if not results:
        await update.message.reply_text("📊 Ҳали натижалар йўқ.")
        return
    lines = ["📊 *Барча натижалар:*\n"]
    for r in results[-50:]:  # last 50
        lines.append(
            f"👤 {r['full_name']}\n"
            f"📍 {r['region']} — {r['post']}\n"
            f"📄 {r['document']}\n"
            f"✅ {r['correct']}/{r['total']} ({r['percent']}%)\n"
            f"🕐 {r['end_time'][:16]}\n"
            f"{'─'*30}"
        )
    text = "\n".join(lines)
    # Split if too long
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000], parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Сиз администратор эмассиз.")
        return
    results = db.get_all_results()
    if not results:
        await update.message.reply_text("📊 Ҳали натижалар йўқ.")
        return
    df_export = pd.DataFrame(results)
    path = "/tmp/export_results.xlsx"
    df_export.to_excel(path, index=False)
    await update.message.reply_document(
        document=open(path, "rb"),
        filename="natijalar.xlsx",
        caption="📊 Барча натижалар Excel форматида."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Бекор қилинди. /start билан қайта бошланг.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULL_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
            REGION:     [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_region)],
            POST:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_post)],
            DOCUMENT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_document)],
            TEST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_count)],
            TESTING:    [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
            AFTER_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_after_test_menu)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🏠 Бош меню$"), home_command),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("export", admin_export))

    logger.info("Бот ишга тушди...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
