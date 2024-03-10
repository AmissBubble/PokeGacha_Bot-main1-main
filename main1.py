from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

import info
import functions
from PokemonBot import PokemonBot


# Загрузка токена из переменных окружения
TOKEN = info.POKE_BOT_API
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

async def main():
    try:
        pokemon_bot = PokemonBot()
        await pokemon_bot.async_init()
        await dp.start_polling()
    finally:
        await bot.session.close()


# Если файл запущен напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Создание экземпляра класса PokemonBot
    pokemon_bot = PokemonBot()


    # Обработчики сообщений и колбеков
    @dp.message_handler(commands=['start'])
    async def start_wrapper(message: types.Message):
        await pokemon_bot.start(message)


    @dp.message_handler(commands=['pokedex'])
    async def deploy_pokedex(message: types.Message):
        chat_id = message.chat.id
        await pokemon_bot.show_pokedex_variations(chat_id, "Select what do you want to see in Pokédex")


    @dp.message_handler(commands=['go'])
    async def show_go_message(message: types.Message):
        chat_id = message.chat.id
        await pokemon_bot.show_go_buttons(chat_id)


    @dp.message_handler(commands=['help'])
    async def help_command(message: types.Message):
        await bot.send_message(message.chat.id, info.HelpInfo, parse_mode='HTML')


    @dp.message_handler(commands=['get_pokebols'])
    async def get_pokebols_handler(message: types.Message):
        await pokemon_bot.get_pokebols(message.chat.id)


    @dp.message_handler(commands=['inventory'])
    async def inventory_handler(message: types.Message):
        await pokemon_bot.show_inventory_variations(message.chat.id)


    @dp.message_handler(commands=['rarity'])
    async def rarity_command(message: types.Message):
        await bot.send_message(message.chat.id, info.RARITY, parse_mode='HTML')


    @dp.callback_query_handler(Text(equals="next"))
    async def scroll_to_next(call: types.CallbackQuery):
        markup = InlineKeyboardMarkup()
        next_list = InlineKeyboardButton('Next', callback_data='next')
        markup.add(next_list)
        try:
            text = await pokemon_bot.generator.__anext__()
            await bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except StopIteration:
            await bot.edit_message_text('This Pokédex is not valid anymore, press /pokedex to get up-to-date version', call.message.chat.id, call.message.message_id)


    @dp.callback_query_handler(Text(equals="All_pokedex"))
    async def show_allpokedex(call: types.CallbackQuery):
        await pokemon_bot.show_all_pokedex(call.message.chat.id, call.message.message_id)


    @dp.callback_query_handler(Text(equals="All_inventory"))
    async def show_all_inventory(call: types.CallbackQuery):
        await pokemon_bot.inventory_all(call.message.chat.id, call.message.message_id)


    @dp.callback_query_handler(Text(endswith='_pokedex'))
    async def show_rariry_pokedex(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        markup = await pokemon_bot.pokedex_markups()
        await bot.edit_message_text(await functions.show_pokedex_rarity(chat_id, call.data[:-8]), chat_id, call.message.message_id, reply_markup=markup)


    @dp.callback_query_handler(Text(endswith='_inventory'))
    async def show_rariry_pokedex(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        markup = await pokemon_bot.inventory_markups()
        await bot.edit_message_text(await functions.show_inventory_rarity(chat_id, call.data[:-10]), chat_id,call.message.message_id, reply_markup=markup)


    @dp.callback_query_handler(Text(equals=['go', 'keepgoing', 'skip', 'retry', 'catch']))
    async def handle_go_callback_wrapper(call: types.CallbackQuery):
        markup = types.InlineKeyboardMarkup()
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
        await pokemon_bot.handle_go_callback(call)


    # Запуск бота
    asyncio.run(main())
