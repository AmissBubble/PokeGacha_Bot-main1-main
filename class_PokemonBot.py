import random

from aiogram import types
import functions
import info
from info import bot, dp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class PokemonBot:

    def __init__(self):
        self.states = {}
        self.generator = None
        self.found_pokemon = ""
        self.rarity_pokemon_count = 1
        self.max_num_in_rarity = 0

    async def async_init(self):
        await functions.create_all_tables()

    async def start(self, message):
        await functions.add_user_to_number_of_pokemons(message.chat.id)
        await bot.send_message(message.chat.id,
                               f"Hi, {message.from_user.first_name}!\nWelcome to Poké-Hunter. This bot allows you to search and catch Pokémons.\nPress /go to start your adventure.\nPress /help for more information.")

    async def handle_go_callback(self, call):
        chat_id = call.message.chat.id  # Для простоты предполагаем, что user_id и chat_id идентичны

        # Используйте `await` для асинхронного получения количества pokebols
        pokebol_count = await functions.pokebols_number(chat_id)

        if pokebol_count > 0:
            # Обработка нажатия кнопок "Go", "Keep going", "Skip"
            if call.data in ['go', 'keepgoing', 'skip']:
                self.found_pokemon = ""
                try:
                    if call.data in ['keepgoing', 'skip']:
                        await bot.delete_message(call.message.chat.id, call.message.message_id)
                    if call.data == 'skip':
                        await bot.delete_message(call.message.chat.id, call.message.message_id - 1)
                except Exception as e:
                    print(f"Ошибка при удалении сообщения: {e}")

                if random.choice([True, False]):
                    await self.show_catch_or_skip_buttons(chat_id, pokebol_count)
                else:
                    await self.back_to_start(chat_id, call.message.message_id)

            # Обработка нажатия кнопок "Catch", "Retry"
            elif call.data in ['catch', 'retry']:
                if call.data == 'retry':
                    await bot.delete_message(call.message.chat.id, call.message.message_id)

                if random.choice([True, False]):

                    await self.show_captured_or_retry_buttons(chat_id, call.message.message_id)

                else:

                    await self.show_captured_or_not_buttons(chat_id, call.message.message_id)


        else:
            await bot.send_message(chat_id,
                                   "У вас нет pokebol! Найдите или купите их, чтобы продолжить ловлю покемонов.")
            # на будущее: нужно придумать какое то продолжение для пользователя после этого сообщения

    async def show_go_buttons(self, chat_id):
        # Отправка кнопки "Go" для начала поиска покемона
        markup = types.InlineKeyboardMarkup()
        button_go = types.InlineKeyboardButton('Go', callback_data='go')
        markup.add(button_go)
        await bot.send_message(chat_id, "Press 'Go' to start searching for a Pokemon:", reply_markup=markup)

    async def back_to_start(self, chat_id, message_id):
        # Возвращение к начальному состоянию после неудачной попытки
        markup = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton('Keep going', callback_data='keepgoing')
        markup.add(button_back)
        await bot.send_message(chat_id, 'You did not find anything', reply_markup=markup)
        # bot.delete_message(chat_id, message_id)

    async def show_pokedex_variations(self, chat_id, text):
        markup = await self.command_markups('pokedex')
        await bot.send_message(chat_id, text, reply_markup=markup)

    async def show_inventory_variations(self, chat_id):
        markup = await self.command_markups('inventory')
        await bot.send_message(chat_id, "Inventory", reply_markup=markup)

    async def show_all_pokedex(self, chat_id, message_id):
        self.generator = functions.show_pokedex_all(chat_id)
        markup = types.InlineKeyboardMarkup()
        next_list = types.InlineKeyboardButton('Next', callback_data='next')
        markup.add(next_list)
        # Используйте pokedex_page для отправки текущего содержимого страницы
        text = await self.generator.__anext__()
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

    async def inventory_all(self, chat_id, message_id):
        self.generator = functions.show_inventory_all(chat_id)
        markup = types.InlineKeyboardMarkup()
        next_list = types.InlineKeyboardButton('Next', callback_data='next')
        markup.add(next_list)
        # Используйте pokedex_page для отправки текущего содержимого страницы
        text = await self.generator.__anext__()
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

    async def show_pictures_rarity(self, user_id: int, rarity: str):
        list_pictures_rarity = await functions.list_pictures_rarity(user_id, rarity)
        self.max_num_in_rarity = len(list_pictures_rarity)
        while True:
            counter = self.rarity_pokemon_count - 1
            pokemon_and_count = list_pictures_rarity[counter]
            yield pokemon_and_count[0], pokemon_and_count[1]
            # pokemon name          #pokemons number in user inventory

    async def show_catch_or_skip_buttons(self, chat_id, pokebol_count):
        # Отображение кнопок "Try to Catch" и "Skip" после успешной попытки
        markup = types.InlineKeyboardMarkup()
        button_catch = types.InlineKeyboardButton('Try to Catch', callback_data='catch')
        button_skip = types.InlineKeyboardButton('Skip', callback_data='skip')
        markup.add(button_catch, button_skip)

        # Отображение случайного покемона с весами
        chosen_pokemon, gen = functions.determine_pokemon()  # функция с вероятностями выпадения покемонов в файле functions.py
        pokemon_image = f'images/{chosen_pokemon.capitalize()}.webp'
        with open(pokemon_image, 'rb') as pokemon_photo:
            self.found_pokemon = chosen_pokemon
            sent_message = await bot.send_document(chat_id, pokemon_photo)
            gen_info = info.GENERATIONS[chosen_pokemon]
            if gen_info != '': gen_info = f' ({gen_info})'
            await bot.send_message(chat_id,
                                   f"You found a {chosen_pokemon}{gen_info}!\n\n It has '{gen}' rarity.\n\n What would you like to do?\n\nYou have {pokebol_count} pokebols",
                                   reply_markup=markup)
            self.states[chat_id] = {'state': 'choose_catch_or_skip', 'message_id': sent_message.message_id, 'gen': gen}

    async def show_captured_or_retry_buttons(self, chat_id, message_id):
        # Отображение кнопки "Keep going" после успешного захвата
        gen = self.states[chat_id].get('gen', '')
        markup = types.InlineKeyboardMarkup()
        button_go = types.InlineKeyboardButton('Keep going', callback_data='go')
        markup.add(button_go)
        await functions.capture_pokemon(chat_id, f"{self.found_pokemon}")
        # await functions.capture_pokemon_by_rarity(chat_id, f"{self.found_pokemon}", gen)

        await bot.send_message(chat_id, f"You captured a {self.found_pokemon}!", reply_markup=markup)

        # bot.delete_message(chat_id, message_id)

    async def increase_and_show_pokemon_picture(self, chat_id, message_id, num, rarity=""):
        if num == 0:
            self.generator = self.show_pictures_rarity(chat_id, rarity)

        elif self.rarity_pokemon_count >= self.max_num_in_rarity:
            self.rarity_pokemon_count = 0

        self.rarity_pokemon_count += num
        pokemon, pokemon_amount = await self.generator.__anext__()
        markup = InlineKeyboardMarkup()
        back = InlineKeyboardButton("<<", callback_data="back")
        number = InlineKeyboardButton(f'{self.rarity_pokemon_count}/{self.max_num_in_rarity}', callback_data="www")
        forward = InlineKeyboardButton(">>", callback_data="forward")
        markup.add(back, number, forward)
        await bot.edit_message_text(f'{pokemon} you have {pokemon_amount}', chat_id, message_id, reply_markup=markup)

    async def decrease_and_show_pokemon_picture(self, chat_id, message_id, num):
        if self.rarity_pokemon_count <= 1:
            self.rarity_pokemon_count = self.max_num_in_rarity + 1
        self.rarity_pokemon_count -= num
        pokemon, pokemon_amount = await self.generator.__anext__()
        markup = InlineKeyboardMarkup()
        back = InlineKeyboardButton("<<", callback_data="back")
        number = InlineKeyboardButton(f'{self.rarity_pokemon_count}/{self.max_num_in_rarity}', callback_data="www")
        forward = InlineKeyboardButton(">>", callback_data="forward")
        markup.add(back, number, forward)
        await bot.edit_message_text(f'{pokemon} you have {pokemon_amount}', chat_id, message_id, reply_markup=markup)

    async def show_captured_or_not_buttons(self, chat_id, message_id):
        # Отображение кнопки "Try again" после неудачной попытки захвата
        markup = types.InlineKeyboardMarkup()
        button_try_again = types.InlineKeyboardButton('Try again', callback_data='retry')
        markup.add(button_try_again)
        await functions.capture_failed(chat_id)
        await bot.send_message(chat_id, 'Bad luck', reply_markup=markup)
        # bot.delete_message(chat_id, message_id)

    async def get_pokebols(self, user_id):
        can_get_pokebols = await functions.check_pokebols_eligibility(user_id)  # возвращает True or False
        text = functions.time_until_next_midnight()
        if can_get_pokebols:
            await functions.add_pokebols(user_id, 50)
            await bot.send_message(user_id,
                                   f'Вы получили 50 бесплатных покеболов. До следующего бесплатного получения осталось {text}')
        else:
            await bot.send_message(user_id,
                                   f'К сожалению вы еще не можете получить бесплатные покеболы. Дождитесь следующего дня. Осталось ждать: {text}')
    async def command_markups(self, command):
        markup = types.InlineKeyboardMarkup()
        all_var = types.InlineKeyboardButton("All", callback_data=f"All_{command}")
        common = types.InlineKeyboardButton("Common", callback_data=f"Common_{command}")
        uncommon = types.InlineKeyboardButton("Uncommon", callback_data=f"Uncommon_{command}")
        rare = types.InlineKeyboardButton("Rare", callback_data=f"Rare_{command}")
        superrare = types.InlineKeyboardButton("SuperRare", callback_data=f"SuperRare_{command}")
        epic = types.InlineKeyboardButton("Epic", callback_data=f"Epic_{command}")
        legendary = types.InlineKeyboardButton("Legendary", callback_data=f"Legendary_{command}")
        markup.add(common, uncommon, rare, superrare, epic, legendary, all_var)
        return markup
    def run(self):
        # Запуск бота в режиме бесконечного опроса
        dp.infinity_polling()
