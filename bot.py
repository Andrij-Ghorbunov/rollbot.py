from telegram import Update, User
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from logic import roll_code
import re

def user_tag(user: User):
    if user.username:
        return '@' + user.username
    name = user.first_name
    if user.last_name:
        name += ' ' + user.last_name
    return f'<a href="tg://user?id={user.id}">{name}</a>'
    pass

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Syntax: /roll #d#t#!=±#. Initial # is number of dice in the pool (1 by default), d# is number of sides in a die (10 by default), "
        + "t# is threshold to count as a success (if not provided - simply counts sum of rolled values), +# or -# modifies the result, ! counts maximal values "
        + "as two successes each, "
        + "= prevents subtraction of 1s from successes. Everything is optional. Roll for hit and roll for damage can be combined with & (in case of threshold, "
        + "exceeding successes from the first roll will be added to the pool of the second one).")

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text[:5] != '/roll':
        await update.message.reply_text(f'Something strange happened')
        return
    code = update.message.text[5:]
    if len(code) and code[0] == '@':
        match = re.search(r'^[\w_]+\b(.*)$', code[1:])
        if not match:
            await update.message.reply_text(f'Something strange happened')
            return
        code = match.group(1)
    reply = roll_code(code)
    if not reply:
        await update.message.reply_text("Wrong syntax, please check /help", parse_mode='HTML')
        return
    reply = user_tag(update.message.from_user) + ' rolled ' + reply
    await update.message.reply_text(reply, parse_mode='HTML')

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update:
        return
    await update.message.reply_text(f'Error')

load_dotenv()
app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

app.add_error_handler(error)
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("roll", roll))

app.run_polling()