import random
from datetime import datetime, timedelta
from aiogram import types
import asyncio
import functions
import energy
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
        self.last_skip_time = {}  # Изменили на словарь для отслеживания времени по chat_id

    async def async_init(self):
        await functions.create_all_tables()

    async def start(self, message):
        await functions.add_user_to_number_of_pokemons(message.chat.id)
        await functions.add_user_and_initialize_energy(message.chat.id)
        await bot.send_message(message.chat.id,
                               f"Hi, {message.from_user.first_name}!\nWelcome to Poké-Hunter. This bot allows you to search and catch Pokémons.\nPress /go to start your adventure.\nPress /help for more information.")

    async def handle_go_callback(self, call):
        chat_id = call.message.chat.id  # Для простоты предполагаем, что user_id и chat_id идентичны

        # Используйте `await` для асинхронного получения количества pokebols
        if call.data == 'skip':
            now = datetime.now()
            if chat_id in self.last_skip_time and now - self.last_skip_time[chat_id] < timedelta(
                    seconds=1):  # Ограничиваем 1 нажатие в 2 секунды

                await self.slow_down(chat_id, call.message.message_id)
                return
            self.last_skip_time[chat_id] = now

        pokebol_count = await functions.pokebols_number(chat_id)
        energy_level = await energy.energy_number(chat_id)

        if pokebol_count > 0 and energy_level > 0:
            # Обработка нажатия кнопок "Go", "Keep going", "Skip"
            if call.data in ['go', 'keepgoing', 'skip']:
                self.found_pokemon = ""
                try:
                    if call.data in ['keepgoing', 'skip']:
                        await bot.delete_message(call.message.chat.id, call.message.message_id)
                    if call.data == 'skip':
                        await bot.delete_message(call.message.chat.id, call.message.message_id - 1)
                except Exception as e:
                    if "message to delete not found" not in str(e).lower():
                        print(f"Ошибка при удалении сообщения: {e}")

                if random.choice([True, False]):
                    await self.show_catch_or_skip_buttons(chat_id, pokebol_count, energy_level)

                else:
                    await self.back_to_start(chat_id, call.message.message_id)

                await energy.use_energy(chat_id)

            # Обработка нажатия кнопок "Catch", "Retry"
            elif call.data in ['catch', 'retry']:
                await self.rarity_catch(call)


        elif pokebol_count <= 0:
            await bot.send_message(chat_id,
                                   "У вас нет pokebol! Найдите или купите их, чтобы продолжить ловлю покемонов.")
            # на будущее: нужно придумать какое то продолжение для пользователя после этого сообщения
        else:
            await self.gain_energy_at_start(chat_id)
            await self.show_catch_or_skip_buttons(chat_id, pokebol_count, energy_level)

    async def rarity_catch(self, call):
        chat_id = call.message.chat.id

        if chat_id in self.states and 'gen' in self.states[chat_id]:
            gen = self.states[chat_id]['gen']

            success_rate = info.POKEMON_CATCH_SUCCESS_RATES[gen]
            success = random.choices([True, False], weights=[success_rate, 100 - success_rate], k=1)[0]
            if call.data == 'retry':
                await bot.delete_message(call.message.chat.id, call.message.message_id)
            if success:
                # Логика для успешного "Catch"
                await self.show_captured_or_retry_buttons(chat_id, call.message.message_id)
            else:
                # Логика для неудачного "Catch", переход к "Retry"
                await self.show_captured_or_not_buttons(chat_id, call.message.message_id)
        else:
            # Если информация о gen отсутствует, обрабатывайте как обычно или сообщите об ошибке
            print(f"No gen info available for chat_id {chat_id}")

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

    async def slow_down(self, chat_id, message_id):
        markup = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton('Keep going', callback_data='keepgoing')
        markup.add(button_back)
        await bot.delete_message(chat_id, message_id)
        await bot.delete_message(chat_id, message_id - 1)
        await bot.send_message(chat_id, "Please slow down", reply_markup=markup)

    async def show_pokedex_variations(self, chat_id, text):
        markup = await self.command_markups('pokedex')
        await bot.send_message(chat_id, text, reply_markup=markup)

    async def show_my_pokemons_variations(self, chat_id):
        markup = await self.command_markups('pokemons')
        await bot.send_message(chat_id, "pokemons", reply_markup=markup)

    async def show_all_pokedex(self, chat_id, message_id):
        self.generator = functions.show_pokedex_all(chat_id)
        markup = types.InlineKeyboardMarkup()
        next_list = types.InlineKeyboardButton('Next', callback_data='next')
        markup.add(next_list)
        text = await self.generator.__anext__()
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

    async def my_pokemons_all(self, chat_id, message_id):
        self.generator = functions.show_my_pokemons_all(chat_id)
        markup = types.InlineKeyboardMarkup()
        next_list = types.InlineKeyboardButton('Next', callback_data='next')
        markup.add(next_list)
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

    async def show_catch_or_skip_buttons(self, chat_id, pokebol_count, energy_level):
        # Отображение кнопок "Try to Catch" и "Skip" после успешной попытки
        markup = types.InlineKeyboardMarkup()
        button_catch = types.InlineKeyboardButton('Try to Catch', callback_data='catch')
        button_skip = types.InlineKeyboardButton('Skip', callback_data='skip')
        markup.add(button_catch, button_skip)

        # Отображение случайного покемона с весами
        chosen_pokemon, gen = functions.determine_pokemon()  # функция с вероятностями выпадения покемонов в файле functions.py

        # Сбор типов для выбранного покемона
        pokemon_types = []
        for type, pokemons in info.POKEMON_BY_TYPE.items():
            if chosen_pokemon in pokemons:
                pokemon_types.append(type)
        pokemon_types_str = ', '.join(pokemon_types) if pokemon_types else 'Unknown'

        pokemon_image = f'images/{chosen_pokemon.capitalize()}.webp'
        with open(pokemon_image, 'rb') as pokemon_photo:
            self.found_pokemon = chosen_pokemon
            sent_message = await bot.send_document(chat_id, pokemon_photo)
            gen_info = info.GENERATIONS.get(chosen_pokemon, '')
            if gen_info:
                gen_info = f' ({gen_info})'
            await bot.send_message(chat_id,
                                   f"You found a {chosen_pokemon}{gen_info}!\nType: {pokemon_types_str}.\n\nIt has '{gen}' rarity.\n\nPokebols:   {pokebol_count}🔴⚪\nEnergy level:   {energy_level}🔋\nCapture chance: {info.POKEMON_CATCH_SUCCESS_RATES[gen]}%",
                                   reply_markup=markup)
            self.states[chat_id] = {'state': 'choose_catch_or_skip', 'message_id': sent_message.message_id, 'gen': gen}

    async def show_captured_or_retry_buttons(self, chat_id, message_id):
        # Отображение кнопки "Keep going" после успешного захвата
        #gen = self.states[chat_id].get('gen', '')
        markup = types.InlineKeyboardMarkup()
        button_go = types.InlineKeyboardButton('Keep going', callback_data='go')
        markup.add(button_go)
        await functions.capture_pokemon(chat_id, f"{self.found_pokemon}")

        await bot.send_message(chat_id, f"You captured a {self.found_pokemon}!", reply_markup=markup)

        # bot.delete_message(chat_id, message_id)
    async def show_first_pokemon_picture(self, chat_id, message_id, rarity: str):
        self.generator = self.show_pictures_rarity(chat_id, rarity)
        self.rarity_pokemon_count = 1
        try:
            pokemon, pokemon_amount = await self.generator.__anext__()
        except:
            markup = InlineKeyboardMarkup()
            return_to_pictures = InlineKeyboardButton("⬅️Go back", callback_data="go_back")
            markup.add(return_to_pictures)
            return await bot.edit_message_text(f"You don't have any {rarity} pokemons yet", chat_id, message_id, reply_markup=markup)

        markup = InlineKeyboardMarkup()
        back = InlineKeyboardButton("<<", callback_data="back")
        number = InlineKeyboardButton(f'{self.rarity_pokemon_count}/{self.max_num_in_rarity}', callback_data="www")
        forward = InlineKeyboardButton(">>", callback_data="forward")
        return_to_pictures = InlineKeyboardButton("⬅️Go back", callback_data="go_back")
        markup.add(back, number, forward, return_to_pictures)
        pokemon_image = f'images/{pokemon}.webp'
        with open(pokemon_image, 'rb') as pokemon_photo:
            await bot.send_photo(chat_id, pokemon_photo, caption=f'1. {pokemon}\nYou have: {pokemon_amount}', reply_markup=markup )


    async def increase_and_show_pokemon_picture(self, chat_id, message_id, num, rarity=""):

        if self.rarity_pokemon_count >= self.max_num_in_rarity:
            self.rarity_pokemon_count = 0

        self.rarity_pokemon_count += num
        pokemon_number_in_sequence = self.rarity_pokemon_count
        pokemon, pokemon_amount = await self.generator.__anext__()
        markup = InlineKeyboardMarkup()
        back = InlineKeyboardButton("<<", callback_data="back")
        number = InlineKeyboardButton(f'{pokemon_number_in_sequence}/{self.max_num_in_rarity}', callback_data="www")
        forward = InlineKeyboardButton(">>", callback_data="forward")
        return_to_pictures = InlineKeyboardButton("⬅️Go back", callback_data="go_back")
        markup.add(back, number, forward, return_to_pictures)
        pokemon_image = f'images/{pokemon}.webp'
        with open(pokemon_image, 'rb') as pokemon_photo:
            new_media = types.InputMediaPhoto(pokemon_photo, caption=f'{pokemon_number_in_sequence}. {pokemon}\nYou have: {pokemon_amount}')
            await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=new_media, reply_markup=markup)

    async def decrease_and_show_pokemon_picture(self, chat_id, message_id, num):
        if self.rarity_pokemon_count <= 1:
            self.rarity_pokemon_count = self.max_num_in_rarity + 1
        self.rarity_pokemon_count -= num
        pokemon_number_in_sequence = self.rarity_pokemon_count
        pokemon, pokemon_amount = await self.generator.__anext__()
        markup = InlineKeyboardMarkup()
        back = InlineKeyboardButton("<<", callback_data="back")
        number = InlineKeyboardButton(f'{self.rarity_pokemon_count}/{self.max_num_in_rarity}', callback_data="www")
        forward = InlineKeyboardButton(">>", callback_data="forward")
        return_to_pictures = InlineKeyboardButton("⬅️Go back", callback_data="go_back")
        markup.add(back, number, forward, return_to_pictures)
        pokemon_image = f'images/{pokemon}.webp'
        with open(pokemon_image, 'rb') as pokemon_photo:
            new_media = types.InputMediaPhoto(pokemon_photo, caption=f'{pokemon_number_in_sequence}. {pokemon}\nYou have: {pokemon_amount}')
            await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=new_media, reply_markup=markup)

    async def show_captured_or_not_buttons(self, chat_id, message_id):
        # Отображение кнопки "Try again" после неудачной попытки захвата
        markup = types.InlineKeyboardMarkup()
        button_try_again = types.InlineKeyboardButton('Try again', callback_data='retry')
        markup.add(button_try_again)
        await functions.capture_failed(chat_id)
        await bot.send_message(chat_id, 'Bad luck', reply_markup=markup)
        # bot.delete_message(chat_id, message_id)

    async def item_handler(self, call):  # использует хлеб
        user_id = call.message.chat.id
        call_data = call.data
        if call_data == 'check_bread':
            has_bread = await energy.check_bread_availability(user_id)  # проверяет наличие хлеба
            if has_bread:
                await energy.use_bread(user_id)
                await call.answer("Вы съели хлеб и восстановили 10 энергии!", show_alert=True)
            else:
                await call.answer("У вас нет предмета Bread!", show_alert=True)
        elif call_data == 'check_rice':
            has_rice = await energy.check_rice_availability(user_id)
            if has_rice:
                await energy.use_rice(user_id)
                await call.answer("Вы съели рис и восстановили 15 энергии!", show_alert=True)
            else:
                await call.answer("У вас нет предмета Rice!", show_alert=True)
        elif call_data == 'check_ramen':
            has_ramen = await energy.check_ramen_availability(user_id)
            if has_ramen:
                await energy.use_ramen(user_id)
                await call.answer("Вы съели рамен и восстановили 25 энергии!", show_alert=True)
            else:
                await call.answer("У вас нет предмета Ramen!", show_alert=True)
        elif call.data == 'check_spaghetti':
            has_spaghetti = await energy.check_spaghetti_availability(user_id)
            if has_spaghetti:
                await energy.use_spaghetti(user_id)
                await call.answer("Вы съели спагетти и восстановили 40 энергии!", show_alert=True)
            else:
                await call.answer("У вас нет предмета Spaghetti!", show_alert=True)

    async def items_buttons(self, chat_id):
        markup = types.InlineKeyboardMarkup()
        button_bread = types.InlineKeyboardButton('🍞Bread', callback_data='check_bread')
        button_rice = types.InlineKeyboardButton('🍚Rice', callback_data='check_rice')
        button_ramen = types.InlineKeyboardButton('🍜Ramen', callback_data='check_ramen')
        button_spaghetti = types.InlineKeyboardButton('🍝Spaghetti', callback_data='check_spaghetti')
        markup.add(button_bread, button_rice, button_ramen, button_spaghetti)
        await bot.send_message(chat_id, 'Item bag', reply_markup=markup)

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

    async def gain_energy(self, user_id):
        can_gain_energy = await energy.check_energy_eligibility(user_id)
        time_until_next_midnight = functions.time_until_next_midnight()
        if can_gain_energy:
            await energy.add_energy(user_id, 20)
            await bot.send_message(user_id,
                                   f'Вы отдохнули, и востоновили 20 энергии. До сдедующего отдыза осталось {time_until_next_midnight}')
        else:
            await bot.send_message(user_id,
                                   f'К сожалению вы еще не можете отдохнуть. Дождитесь следующего дня. Осталось ждать: {time_until_next_midnight}')

    async def gain_energy_at_start(self, user_id):
        can_gain_energy = await energy.check_last_adventure(user_id)
        time_until_next_midnight = functions.time_until_next_midnight()
        if can_gain_energy:
            await energy.add_energy(user_id, 30)
            await bot.send_message(user_id,
                                   f'Вы отдохнули, и востоновили 30 энергии. До сдедующего отдыха осталось {time_until_next_midnight}')

        else:
            await bot.send_message(user_id,
                                   f'К сожалению сегодня вы израсходовали всю энергию. Вы можете отдохнуть, восполнить энергию едой, либо дождатся следующего дня. Осталось ждать: {time_until_next_midnight}')

    def run(self):
        # Запуск бота в режиме бесконечного опроса
        dp.infinity_polling()
