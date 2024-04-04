from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified, BadRequest
import asyncio
from class_reply import under_keyboard
import info
import functions
import energy
from class_PokemonBot import PokemonBot
from aiogram.utils.exceptions import MessageNotModified

# Загрузка токена из переменных окружения
from info import bot, dp
under_keyboard_class = under_keyboard()


users_bot = {}

async def main():
    try:
        await functions.create_all_tables()
        await dp.start_polling()
    finally:
        await bot.session.close()


async def create_bot_class_for_user(user_id):
    global users_bot
    if user_id not in users_bot:
        users_bot[user_id] = PokemonBot()


if __name__ == "__main__":
    # Создание экземпляра класса PokemonBot
    pokemon_bot = PokemonBot()
    # Обработчики сообщений и колбеков
    @dp.message_handler(commands=['start'])
    async def start_wrapper(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].start(message)
        #await pokemon_bot.start(message)


    @dp.message_handler(commands=['📱Pokedex'])
    async def deploy_pokedex(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].show_pokedex_variations(chat_id, "Select what do you want to see in Pokédex")


    @dp.message_handler(commands=['🏃‍♂️Start_Adventure'])
    async def show_go_message(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].gain_energy_at_start(chat_id)
        await users_bot[chat_id].show_go_buttons(chat_id)
    
    @dp.message_handler(commands=['🔚End_Adventure'])
    async def show_menu_message(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].del_last_go_message(message)


    @dp.message_handler(commands=['help'])
    async def help_command(message: types.Message):
        await bot.send_message(message.chat.id, info.HelpInfo, parse_mode='HTML')


    @dp.message_handler(commands=['🔴⚪Get_Pokebolls'])
    async def get_pokebols_handler(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].get_pokebols(chat_id)


    @dp.message_handler(commands=['have_a_rest'])
    async def get_energy_handler(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].gain_energy(message.chat.id)


    @dp.message_handler(commands=['🎒My_pokemons'])
    async def my_pokemons_handler(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        keyboard = users_bot[chat_id].my_pokemons_keyboard()
        await message.answer("Выберите, как вы хотите просмотреть своих покемонов:", reply_markup=keyboard)
    

    @dp.message_handler(commands=['🍽️Meal'])
    async def items_handler(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].items_buttons(message.chat.id)


    @dp.message_handler(commands=['rarity'])
    async def rarity_command(message: types.Message):
        await bot.send_message(message.chat.id, info.RARITY, parse_mode='HTML')


    @dp.callback_query_handler(Text(equals='🖼️pictures')) #🖼️
    async def see_in_pictures(message: types.Message):
        chat_id = message.chat.id
        await create_bot_class_for_user(chat_id)
        markups = await users_bot[chat_id].command_markups('pictures')
        await bot.send_message(message.chat.id, "Choose the rarity you want to see", reply_markup=markups)

    @dp.callback_query_handler(lambda c: c.data == 'view_list')
    async def show_pokemon_list(callback_query: types.CallbackQuery):
        chat_id = callback_query.message.chat.id
        await create_bot_class_for_user(chat_id)
        message_id = callback_query.message.message_id
        await bot.delete_message(chat_id, message_id)
        await users_bot[chat_id].show_my_pokemons_variations(chat_id)
        await bot.answer_callback_query(callback_query.id)  ##?????????

    @dp.callback_query_handler(lambda c: c.data == 'view_photos')
    async def show_pokemon_photos(callback_query: types.CallbackQuery):
        chat_id = callback_query.message.chat.id
        await create_bot_class_for_user(chat_id)
        message_id = callback_query.message.message_id
        await bot.delete_message(chat_id, message_id)
        markups = await users_bot[chat_id].command_markups('pictures')
        await bot.send_message(callback_query.message.chat.id, "Choose the rarity you want to see", reply_markup=markups)
        


    @dp.callback_query_handler(Text(equals="next"))
    async def scroll_to_next(call: types.CallbackQuery):
        markup = InlineKeyboardMarkup()
        next_list = InlineKeyboardButton('Next', callback_data='next')
        markup.add(next_list)
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        try:
            text = await users_bot[chat_id].generator.__anext__()
            await bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        except StopIteration:
            await bot.edit_message_text('This Item is not valid anymore, press /📱Pokedex to get up-to-date version',
                                        chat_id, call.message.message_id)
        except MessageNotModified:
            pass


    @dp.callback_query_handler(Text(equals="All_pokedex"))
    async def show_allpokedex(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].show_all_pokedex(chat_id, call.message.message_id)


    @dp.callback_query_handler(Text(equals="All_pokemons"))
    async def show_all_my_pokemons(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].my_pokemons_all(chat_id, call.message.message_id)


    @dp.callback_query_handler(Text(endswith='_pokedex'))
    async def show_rariry_pokedex(call):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        markup = await users_bot[chat_id].command_markups('pokedex')
        await bot.edit_message_text(await functions.show_pokedex_rarity(chat_id, call.data[:-8]), chat_id,
                                    call.message.message_id, reply_markup=markup)


    @dp.callback_query_handler(Text(endswith='_pokemons'))
    async def show_rarity_pokemons(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        markup = await users_bot[chat_id].command_markups('pokemons')
        await bot.edit_message_text(await functions.show_pokemons_rarity(chat_id, call.data[:-9]), chat_id,
                                    call.message.message_id, reply_markup=markup)


    @dp.callback_query_handler(Text(endswith='_pictures'))
    async def show_rarity_pictures(call):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].show_first_pokemon_picture(chat_id, call.message.message_id, call.data[:-9])


    @dp.callback_query_handler(Text(equals='forward'))
    async def change_pokemon_picture(call):
        chat_id = call.message.chat.id
        try:
            await users_bot[chat_id].increase_and_show_pokemon_picture(call.message.chat.id, call.message.message_id, 1)
        except MessageNotModified:
            pass
        except BadRequest:
            await bot.send_message(chat_id, "Please slow down, bot cannot process quick button presses")


    @dp.callback_query_handler(Text(equals='back'))
    async def change_pokemon_picture(call):
        chat_id = call.message.chat.id
        try:
            await users_bot[chat_id].decrease_and_show_pokemon_picture(chat_id, call.message.message_id, 1)
        except MessageNotModified:
            pass
        except BadRequest:
            await bot.send_message(chat_id, "Please slow down, bot cannot process quick button presses")


    @dp.callback_query_handler(Text(equals='go_back'))
    async def go_to_pictures_start(call):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        await bot.delete_message(chat_id, call.message.message_id)
        markups = await users_bot[chat_id].command_markups('pictures')
        await bot.send_message(chat_id, "Choose the rarity you want to see", reply_markup=markups)

    @dp.callback_query_handler(Text(equals=['🏃‍♂️Start_Adventure', 'keepgoing', 'skip', 'retry', 'catch']))
    async def handle_go_callback_wrapper(call: types.CallbackQuery):
        markup = types.InlineKeyboardMarkup()
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        await bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
        await users_bot[chat_id].handle_go_callback(call)


    @dp.callback_query_handler(
        Text(equals=['check_bread', 'check_rice', 'check_ramen', 'check_spaghetti']))  # обрабатывает колбэк
    async def handle_check_bread(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        await users_bot[chat_id].item_handler(call)  # использует хлеб

    @dp.callback_query_handler(lambda c: c.data == 'use_candy')
    async def use_candy(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        await create_bot_class_for_user(chat_id)
        result = await users_bot[chat_id].candy_button(call)  # Вызов метода, который проверяет и использует Candy
        if result:
            # Увеличиваем счетчик использований "Candy" на 1 или инициализируем его, если не было использований
            users_bot[chat_id].candy_usage += 1
            
        


    # Запуск бота
    asyncio.run(main())
