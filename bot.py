import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    filters, ContextTypes,
)
import pandas as pd
from database import Database

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

(FULL_NAME, REGION, POST, DOCUMENT, TEST_COUNT, TESTING, AFTER_TEST) = range(7)

REGIONS_POSTS = {
    "Тошкент шахар": [
        "Тошкент шаҳри бўйича бошқармаси",
        "«Тошкент-товар» ТИФ божхона пости",
        "«Арк булоқ» ТИФ божхона пости",
        "«Чуқурсой» ТИФ божхона пости",
        "«Келес» темир йўл чегара божхона пости",
        "«Сирғали» ТИФ божхона пости",
        "«Чуқурсой техник идора» темир йўл чегара божхона пости",
    ],
    "«Тошкент-АЭРО»": [
        "«Тошкент-АЭРО» ихтисослаштирилган божхона комплекси",
        "«Ислом Каримов номидаги Тошкент халқаро аэропорти» чегара божхона пости",
        "«Авиа юклар» ТИФ божхона пости",
        "«Электрон тижорат» ТИФ божхона пости",
        "«Тошкент-Ҳумо аэропорти» чегара божхона пости",
    ],
    "Тошкент вилояти": [
        "Тошкент вилояти бўйича бошқармаси",
        "«Яллама» чегара божхона пости",
        "«Навоий» чегара божхона пости",
        "«С. Нажимов» чегара божхона пости",
        "«Ойбек» чегара божхона пости",
        "«Бекобод авто» чегара божхона пости",
        "«Чирчиқ» ТИФ божхона пости",
        "«Олмалиқ» ТИФ божхона пости",
        "«Янгийўл» ТИФ божхона пости",
        "«Назарбек» ТИФ божхона пости",
        "«Келес» ТИФ божхона пости",
        "«Ғишткўприк» чегара божхона пости",
        "«Фарҳод» чегара божхона пости",
        "«Бекобод» темир йўл чегара божхона пости",
        "«Ангрен» ТИФ божхона пости",
    ],
    "Самарқанд": [
        "Самарқанд вилояти бўйича бошқармаси",
        "«Самарқанд аэропорти» чегара божхона пости",
        "«Жартепа» чегара божхона пости",
        "«Самарқанд» ТИФ божхона пости",
        "«Улуғбек» ТИФ божхона пости",
    ],
    "Навоий": [
        "Навоий вилояти бўйича бошқармаси",
        "«Навоий аэропорти» чегара божхона пости",
        "«Навоий» ТИФ божхона пости",
        "«Зарафшон» ТИФ божхона пости",
    ],
    "Фарғона": [
        "Фарғона вилояти бўйича бошқармаси",
        "«Фарғона аэропорти» чегара божхона пости",
        "«Қўқон» ТИФ божхона пости",
        "«Фарғона» чегара божхона пости",
        "«Андархон» чегара божхона пости",
        "«Риштон» чегара божхона пости",
        "«Ровот» чегара божхона пости",
        "«Водий» ТИФ божхона пости",
        "«Ўзбекистон» чегара божхона пости",
        "«Сўх» чегара божхона пости",
    ],
    "Андижон": [
        "Андижон вилояти бўйича бошқармаси",
        "«Дўстлик» чегара божхона пости",
        "«Андижон аэропорти» чегара божхона пости",
        "«Мингтепа» чегара божхона пости",
        "«Қорасув» чегара божхона пости",
        "«Хонобод» чегара божхона пости",
        "«Пушмон» чегара божхона пости",
        "«Маданият» чегара божхона пости",
        "«Андижон» ТИФ божхона пости",
        "«Кесканёр» чегара божхона пости",
        "«Савай» темир йўл чегара божхона пости",
        "«Асака» ТИФ божхона пости",
    ],
    "Наманган": [
        "Наманган вилояти бўйича бошқармаси",
        "«Наманган аэропорти» чегара божхона пости",
        "«Учқўрғон» чегара божхона пости",
        "«Косонсой» чегара божхона пости",
        "«Поп» чегара божхона пости",
        "«Наманган» ТИФ божхона пости",
    ],
    "Сирдарё": [
        "Сирдарё вилояти бўйича бошқармаси",
        "«Ховособод» чегара божхона пости",
        "«Сирдарё» чегара божхона пости",
        "«Оқ олтин» чегара божхона пости",
        "«Гулистон» ТИФ божхона пости",
        "«Малик» чегара божхона пости",
    ],
    "Жиззах": [
        "Жиззах вилояти бўйича бошқармаси",
        "«Учтўрғон» чегара божхона пости",
        "«Жиззах» ТИФ божхона пости",
        "«Қўшкент» чегара божхона пости",
    ],
    "Қашқадарё": [
        "Қашқадарё вилояти бўйича бошқармаси",
        "«Насаф» ТИФ божхона пости",
        "«Қамаши-Ғузор» ТИФ божхона пости",
        "«Қарши-Керки» чегара божхона пости",
        "«Қарши аэропорти» чегара божхона пости",
    ],
    "Сурхондарё": [
        "Сурхондарё вилояти бўйича бошқармаси",
        "«Термиз аэропорти» чегара божхона пости",
        "«Сариосиё» чегара божхона пости",
        "«Сариосиё» темир йўл чегара божхона пости",
        "«Термиз» ТИФ божхона пости",
        "«Денов» ТИФ божхона пости",
        "«Дарё порти» чегара божхона пости",
        "«Болдир» темир йўл чегара божхона пости",
        "«Айритом» чегара божхона пости",
        "«Термиз халқаро савдо маркази» ТИФ божхона пости",
    ],
    "Бухоро": [
        "Бухоро вилояти бўйича бошқармаси",
        "«Бухоро аэропорти» чегара божхона пости",
        "«Бухоро» ТИФ божхона пости",
        "«Қоракўл» ТИФ божхона пости",
        "«Олот» чегара божхона пости",
        "«Хўжадавлат» темир йўл чегара божхона пости",
    ],
    "Қорақалпоғистон Республикаси": [
        "Қорақалпоғистон Республикаси бўйича бошқармаси",
        "«Нукус аэропорти» чегара божхона пости",
        "«Нукус» ТИФ божхона пости",
        "«Хўжайли» чегара божхона пости",
        "«Қорақалпоғистон» темир йўл чегара божхона пости",
        "«Довут-ота» чегара божхона пости",
    ],
    "Хоразм": [
        "Хоразм вилояти бўйича бошқармаси",
        "«Шовот» чегара божхона пости",
        "«Дўстлик» чегара божхона пости",
        "«Урганч» ТИФ божхона пости",
        "«Урганч аэропорти» чегара божхона пости",
        "«Шовот чегараолди савдо зонаси» чегара божхона пости",
    ],
}

db = Database()
df_all = pd.read_excel("tests.xlsx").dropna(subset=["question"])
# Барча матн колонкаларини strip қиламиз — бўшлиқ муаммосини ҳал қилади
for col in ["option_1", "option_2", "option_3", "option_4", "correct_answer"]:
    df_all[col] = df_all[col].astype(str).str.strip()
DOCUMENTS = sorted(df_all["document"].dropna().unique().tolist())


# ─── Helpers ─────────────────────────────────────────────────────────────────
def chunk_text(text, max_len=4000):
    """Узун матнни бўлаклайди"""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]


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
        f"✅ Раҳмат, {name}!\n\nИлтимос, бошқармангизни танланг:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return REGION


async def handle_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "⬅️ Орқага":
        await update.message.reply_text("Исмингизни қайта киритинг:", reply_markup=ReplyKeyboardRemove())
        return FULL_NAME
    if text not in REGIONS_POSTS:
        await update.message.reply_text("❗ Рўйхатдан бошқармани танланг:")
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
        await update.message.reply_text("Бошқармани танланг:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
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

    # Вариантларни strip қиламиз
    options_raw = {
        "option_1": str(q.get("option_1", "")).strip(),
        "option_2": str(q.get("option_2", "")).strip(),
        "option_3": str(q.get("option_3", "")).strip(),
        "option_4": str(q.get("option_4", "")).strip(),
    }
    # Бўш ва "nan" ларни чиқарамиз
    options_clean = {k: v for k, v in options_raw.items() if v and v != "nan"}

    # Тўғри жавоб — option_key орқали матн оламиз
    ca_key = str(q.get("correct_answer", "")).strip()  # "option_2"
    correct_text = options_raw.get(ca_key, "").strip()

    context.user_data["correct_answer"] = correct_text
    context.user_data["options_map"] = options_clean  # key->text

    # Telegram кнопка учун: узун матн (>64 белги) ni қисқартирмаймиз,
    # балки рақам (А, Б, В, Г) ишлатамиз ва матнни саволда кўрсатамиз
    labels = ["А", "Б", "В", "Г"]
    option_keys = list(options_clean.keys())

    # Вариантларни савол матнида кўрсатамиз
    options_text = ""
    for i, key in enumerate(option_keys):
        options_text += f"\n{labels[i]}) {options_clean[key]}"

    # Кнопкалар учун фақат А, Б, В, Г ҳарфлари
    keyboard_buttons = [[labels[i] for i in range(len(option_keys))]]

    # Кнопка → option_key ва матн харитаси
    context.user_data["label_to_key"] = {labels[i]: option_keys[i] for i in range(len(option_keys))}
    context.user_data["label_to_text"] = {labels[i]: options_clean[option_keys[i]] for i in range(len(option_keys))}

    msg = (
        f"📝 Савол {idx+1}/{total}\n"
        f"{'─'*30}\n"
        f"{q['question']}\n"
        f"{'─'*30}"
        f"{options_text}"
    )

    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True, one_time_keyboard=True)
    )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    label_to_text = context.user_data.get("label_to_text", {})
    label_to_key = context.user_data.get("label_to_key", {})
    correct_answer = context.user_data.get("correct_answer", "")
    valid_labels = list(label_to_text.keys())

    if text not in valid_labels:
        await update.message.reply_text(
            f"❗ Илтимос, {', '.join(valid_labels)} дан бирини танланг:"
        )
        return TESTING

    chosen_text = label_to_text[text]
    is_correct = chosen_text.strip() == correct_answer.strip()

    if is_correct:
        context.user_data["correct"] += 1
        feedback = "✅ Тўғри жавоб!"
    else:
        context.user_data["wrong"] += 1
        feedback = f"❌ Нотўғри!\n✅ Тўғри жавоб: {correct_answer}"

    await update.message.reply_text(feedback, reply_markup=ReplyKeyboardRemove())

    context.user_data["current_q"] += 1
    next_idx = context.user_data["current_q"]

    if next_idx >= len(context.user_data["questions"]):
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
        grade = "⭐⭐⭐ Аъло"
    elif percent >= 70:
        grade = "⭐⭐ Яхши"
    elif percent >= 50:
        grade = "⭐ Қониқарли"
    else:
        grade = "❌ Қониқарсиз"

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

    keyboard = ReplyKeyboardMarkup([["🔁 Қайта ечиш", "🏠 Бош меню"]], resize_keyboard=True)
    context.user_data["state"] = "after_test"
    await update.message.reply_text(result_text, reply_markup=keyboard)


async def handle_after_test_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "🔁 Қайта ечиш":
        context.user_data["state"] = None
        doc = context.user_data.get("document", "")
        count = context.user_data.get("test_count", 0)
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


# ─── Админ ────────────────────────────────────────────────────────────────────
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Сиз администратор эмассиз.")
        return
    results = db.get_all_results()
    if not results:
        await update.message.reply_text("📊 Ҳали натижалар йўқ.")
        return
    lines = ["📊 Барча натижалар:\n"]
    for r in results[-50:]:
        lines.append(
            f"👤 {r['full_name']}\n"
            f"📍 {r['region']} — {r['post']}\n"
            f"📄 {r['document']}\n"
            f"✅ {r['correct']}/{r['total']} ({r['percent']}%)\n"
            f"🕐 {r['end_time'][:16]}\n"
            f"{'─'*30}"
        )
    full_text = "\n".join(lines)
    for chunk in chunk_text(full_text):
        await update.message.reply_text(chunk)


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
