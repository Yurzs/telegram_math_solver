import os
import asyncio
from aiogram import Dispatcher, Bot

loop = asyncio.get_event_loop()

bot_token = os.environ.get('BOT_TOKEN')

bot = Bot(token=bot_token)
dp = Dispatcher(bot)
