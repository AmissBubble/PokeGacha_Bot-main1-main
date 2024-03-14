import random
from datetime import datetime, timedelta
from aiogram import types
import functions
import info
from info import bot, dp


class PokemonBot:

    def __init__(self):
        self.states = {}
        self.generator = None
        self.found_pokemon = ""
        self.last_skip_time = {}  # Изменили на словарь для отслеживания времени по chat_id

    async def async_init(self):
        await functions.create_all_tables()

    async def start(self, message):
        await functions.add_user_to_number_of_pokemons(message.chat.id)
        await functions.add_user_and_initialize_energy(message.chat.id)
        await bot.send_message(message.chat.id,
                               f"Hi, {message.from_user.first_name}!\nWelcome to Poké-Hunter. This bot allows you to search and catch Pokémons.\nPress /go to start your adventure.\nPress /help for more information.")

    async def pokedex_markups(self):
        markup = types.InlineKeyboardMarkup()
        all_var = types.InlineKeyboardButton("All", callback_data="All_pokedex")
        common = types.InlineKeyboardButton("Common", callback_data="Common_pokedex")
        uncommon = types.InlineKeyboardButton("Uncommon", callback_data="Uncommon_pokedex")
        rare = types.InlineKeyboardButton("Rare", callback_data="Rare_pokedex")
        superrare = types.InlineKeyboardButton("SuperRare", callback_data="SuperRare_pokedex")
        epic = types.InlineKeyboardButton("Epic", callback_data="Epic_pokedex")
        legendary = types.InlineKeyboardButton("Legendary", callback_data="Legendary_pokedex")
        markup.add(common, uncommon, rare, superrare, epic, legendary, all_var)
        return markup

    async def inventory_markups(self):
        markup = types.InlineKeyboardMarkup()
        all_var = types.InlineKeyboardButton("All", callback_data="All_inventory")
        common = types.InlineKeyboardButton("Common", callback_data="Common_inventory")
        uncommon = types.InlineKeyboardButton("Uncommon", callback_data="Uncommon_inventory")
        rare = types.InlineKeyboardButton("Rare", callback_data="Rare_inventory")
        superrare = types.InlineKeyboardButton("SuperRare", callback_data="SuperRare_inventory")
        epic = types.InlineKeyboardButton("Epic", callback_data="Epic_inventory")
        legendary = types.InlineKeyboardButton("Legendary", callback_data="Legendary_inventory")
        markup.add(common, uncommon, rare, superrare, epic, legendary, all_var)
        return markup

    async def handle_go_callback(self, call):
        chat_id = call.message.chat.id  # Для простоты предполагаем, что user_id и chat_id идентичны

        # Используйте `await` для асинхронного получения количества pokebols
        pokebol_count = await functions.pokebols_number(chat_id)
        if call.data == 'skip':
            now = datetime.now()
            if chat_id in self.last_skip_time and now - self.last_skip_time[chat_id] < timedelta(seconds=1):  # Ограничиваем 1 нажатие в 2 секунды
                
                await self.slow_down(chat_id, call.message.message_id)
                return
            self.last_skip_time[chat_id] = now

        pokebol_count = await functions.pokebols_number(chat_id)
        energy = await functions.energy_number(chat_id)

        if pokebol_count > 0 and energy >0:
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
                    await self.show_catch_or_skip_buttons(chat_id, pokebol_count, energy)
                    await functions.use_energy(chat_id)
                    
                else:
                    await self.back_to_start(chat_id, call.message.message_id)
                    await functions.use_energy(chat_id)

            # Обработка нажатия кнопок "Catch", "Retry"
            elif call.data in ['catch', 'retry']:
                if call.data == 'retry':
                    await bot.delete_message(call.message.chat.id, call.message.message_id)

                if random.choice([True, False]):

                    await self.show_captured_or_retry_buttons(chat_id, call.message.message_id)

                else:

                    await self.show_captured_or_not_buttons(chat_id, call.message.message_id)


        elif pokebol_count<0:
            await bot.send_message(chat_id,
                                   "У вас нет pokebol! Найдите или купите их, чтобы продолжить ловлю покемонов.")
            # на будущее: нужно придумать какое то продолжение для пользователя после этого сообщения
        else:
            await self.gain_energy_at_start(chat_id)
            await self.show_catch_or_skip_buttons(chat_id, pokebol_count, energy)
    

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
        markup = await self.pokedex_markups()
        await bot.send_message(chat_id, text, reply_markup=markup)

    async def show_inventory_variations(self, chat_id):
        markup = await self.inventory_markups()
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

    async def show_catch_or_skip_buttons(self, chat_id, pokebol_count, energy):
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
                                   f"You found a {chosen_pokemon}{gen_info}!\n\n It has '{gen}' rarity.\n\n What would you like to do?\n\nYou have {pokebol_count} pokebols\n\n your energy level is {energy}",
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

    async def show_captured_or_not_buttons(self, chat_id, message_id):
        # Отображение кнопки "Try again" после неудачной попытки захвата
        markup = types.InlineKeyboardMarkup()
        button_try_again = types.InlineKeyboardButton('Try again', callback_data='retry')
        markup.add(button_try_again)
        await functions.capture_failed(chat_id)
        await bot.send_message(chat_id, 'Bad luck', reply_markup=markup)
        # bot.delete_message(chat_id, message_id)


    async def item_handler(self, call): # использует хлеб
        chat_id = call.message.chat.id
        if call.data == 'check_bread':
            await functions.use_bread(chat_id)



    async def items_buttons(self, chat_id):
        markup = types.InlineKeyboardMarkup()
        button_bread = types.InlineKeyboardButton('🍞Bread', callback_data='check_bread')
        markup.add(button_bread)
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
    
    async def gain_energy(self, user_id):
        can_gain_energy = await functions.check_energy_eligibility(user_id)
        text1 = functions.time_until_next_midnight()
        if can_gain_energy:
            await functions.add_energy(user_id, 20)
            await bot.send_message(user_id, f'Вы отдохнули, и востоновили 20 энергии. До сдедующего отдыза осталось {text1}')
        else:
            await bot.send_message(user_id,
                                   f'К сожалению вы еще не можете отдохнуть. Дождитесь следующего дня. Осталось ждать: {text1}')

    async def gain_energy_at_start(self, user_id):
        can_gain_energy1 = await functions.check_last_adventure(user_id)
        text2 = functions.time_until_next_midnight()
        if can_gain_energy1:
            await functions.add_energy(user_id, 30)
            await bot.send_message(user_id, f'Вы отдохнули, и востоновили 30 энергии. До сдедующего отдыха осталось {text2}')
            
        else:
            await bot.send_message(user_id,
                                   f'К сожалению сегодня вы израсходовали всю энергию. Вы можете отдохнуть, восполнить энергию едой, либо дождатся следующего дня. Осталось ждать: {text2}')
        
    

    def run(self):
        # Запуск бота в режиме бесконечного опроса
        dp.infinity_polling()
