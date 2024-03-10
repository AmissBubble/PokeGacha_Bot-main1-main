import random
import asyncio
import aiosqlite
from datetime import datetime, timedelta

from info import POKEMON_LIST, RARITY_DICT, GenerationProbabilities


def pokemon_catch():  # возвращает рандомное имя покемона в зависимости от их вероятности выпадения


    rand_num = random.randint(1, 1000) # вероятности должны в сумме давать 1000
    counter = 0
    for key in GenerationProbabilities:
        counter += int(GenerationProbabilities[key])
        if counter >= rand_num:
            pokemon_name = random.choice(RARITY_DICT[key])
            return pokemon_name, key


class AsyncDatabaseConnection:
    def __init__(self, db_name):
        self.db_name = db_name

    async def __aenter__(self):
        self.conn = await aiosqlite.connect(self.db_name)
        return await self.conn.cursor()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.commit()
        await self.conn.close()




async def create_all_tables():
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        text = "CREATE TABLE IF NOT EXISTS number_of_pokemons (user_id INTEGER, last_access_date VARCHAR(12) DEFAULT '10/12/15', pokebols INTEGER DEFAULT 5, "
        text += "".join(f'{item.lower()} INTEGER DEFAULT 0,' for item in POKEMON_LIST)
        text = text.rstrip(',') + ")"
        await cur.execute(text)
        await cur.execute('''
            CREATE TABLE IF NOT EXISTS captured_pokemons (
            user_id INTEGER,
            found_pokemon VARCHAR(20),
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        await cur.execute('CREATE TABLE IF NOT EXISTS users (name varchar(50))')
        await cur.execute('''CREATE TABLE IF NOT EXISTS dif_rarity 
                    (user_id INTEGER,
                     legendary VARCHAR(30),
                     epic VARCHAR(30),
                     superrare VARCHAR(30),
                     rare VARCHAR(30),
                     uncommon VARCHAR(30),
                     common VARCHAR(30)
                    )''')

async def add_user_to_number_of_pokemons(user_id):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        check_query = 'SELECT * FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(check_query, (user_id,))
        result = await cur.fetchone()
        if result is None:
            insert_query = "INSERT INTO number_of_pokemons (user_id) VALUES (?)"
            await cur.execute(insert_query, (user_id,))



async def capture_pokemon(user_id, found_pokemon):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        num = 'SELECT pokebols FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num, (user_id,))
        pokebol_count = (await cur.fetchone())[0]

        if pokebol_count > 0:
            found_pokemon = found_pokemon.lower()
            cap = "INSERT INTO captured_pokemons (user_id, found_pokemon) VALUES (?, ?)"
            await cur.execute(cap, (user_id, found_pokemon))
            query = f"UPDATE number_of_pokemons SET {found_pokemon} = {found_pokemon} + 1, pokebols = pokebols - 1 WHERE user_id = ?"
            await cur.execute(query, (user_id,))
            success = True
        else:
            success = False
    return success

async def capture_pokemon_by_rarity(user_id, found_pokemon, gen): #все еще не понимаю зачем эта функция
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        # Проверяем количество pokebols у пользователя
        num = 'SELECT pokebols FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num, (user_id,))
        pokebol_count = await cur.fetchone()

        if pokebol_count and pokebol_count[0] > 0:
            found_pokemon = found_pokemon.lower()
            # Выполняем логику захвата в зависимости от редкости
            capture_query = None
            if gen == 'Common':
                capture_query = "INSERT INTO dif_rarity (user_id, common) VALUES (?, ?)"
            elif gen == 'Uncommon':
                capture_query = "INSERT INTO dif_rarity (user_id, uncommon) VALUES (?, ?)"
            elif gen == 'Rare':
                capture_query = "INSERT INTO dif_rarity (user_id, rare) VALUES (?, ?)"
            elif gen == 'SuperRare':
                capture_query = "INSERT INTO dif_rarity (user_id, superrare) VALUES (?, ?)"
            elif gen == 'Epic':
                capture_query = "INSERT INTO dif_rarity (user_id, epic) VALUES (?, ?)"
            elif gen == 'Legendary':
                capture_query = "INSERT INTO dif_rarity (user_id, legendary) VALUES (?, ?)"

            if capture_query:
                await cur.execute(capture_query, (user_id, found_pokemon))
                success = True
            else:
                success = False
        else:
            success = False

    return success

async def capture_failed (user_id):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        pok = 'SELECT pokebols FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(pok, (user_id,))
        pokebol_count = await cur.fetchone()
        pokebol_count = pokebol_count[0]
        if pokebol_count > 0:
            num2 = "UPDATE number_of_pokemons SET pokebols = pokebols - 1 WHERE user_id = ?"
            await cur.execute(num2, (user_id,))


async def show_capture_time(user_id): #показывает время когда словил каждого покемона
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        cap1 = 'SELECT * FROM captured_pokemons WHERE user_id = ?'
        await cur.execute(cap1, (user_id,))
        info = await cur.fetchall()
        pokedex = ''
        for el in info:
            # Убедитесь, что здесь правильно форматируете строку, например:
            pokedex += f"Pokemon: {el[1]}, Captured At: {el[2]}\n"

    return pokedex


async def show_pokedex_all(user_id):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        num3 = 'SELECT * FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num3, (user_id,))
        #собирает всю информацию о покемонах и конкатенирует все в лист_lines_list
        pokemon_amount = await cur.fetchone()
        pokemon_amount = pokemon_amount[3:]
        pokemons = (f'{pokemon} {"🟢" if amount>0 else "🔴"}' for pokemon, amount in zip(POKEMON_LIST, pokemon_amount))
        lines = (f"{num}. {pokemon}" for num, pokemon in enumerate(pokemons, 1))
        lines_list = list(lines)
        while True:
            #разбивает лист на равные куски по 25 покемонов, (последний кусок 26) и возвращает ганератор с нужным текстом
            for chunk_start in range(0, 150, 25):
                if chunk_start == 125:
                    yield '\n'.join(lines_list[chunk_start : chunk_start + 26])
                else:
                    yield '\n'.join(lines_list[chunk_start : chunk_start + 25])


async def show_pokedex_rarity(user_id, requested_rarity):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        num = 'SELECT * FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num, (user_id,))
        pokemon_amount = await cur.fetchone()
        pokemon_amount = pokemon_amount[3:]
        pokemons_in_requested_rarity = ("\n".join(f'{pokemon} {"🟢" if amount>0 else "🔴"}' for pokemon, amount in zip(
            POKEMON_LIST, pokemon_amount) if pokemon in RARITY_DICT[requested_rarity]))


    return pokemons_in_requested_rarity

async def inventory_all(user_id):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        num4 = 'SELECT * FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num4, (user_id,))
        pokemons = await cur.fetchone()

        start = [f'You have:\nPokebols: {pokemons[2]}']
        pokemons_amount = (f'{pokemon_name}: {poke_count}' for poke_count, pokemon_name in zip(pokemons[3:],
                                                                                               POKEMON_LIST) if poke_count > 0)
        text = start + [f'{num}. {pokemon}' for num, pokemon in enumerate(pokemons_amount, 1)]
        lenght = len(text)
        max = 20
        if lenght <= max:
            while True:
                yield "\n".join(text)

        else:
            amount_of_tables = (lenght // max) + 1
            pokemon_amount_in_each_table = (lenght // amount_of_tables) + 1
            while True:
                for chunk_start in range(0, lenght, pokemon_amount_in_each_table):
                    yield '\n'.join(text[chunk_start: chunk_start + pokemon_amount_in_each_table])



async def show_inventory_rarity(user_id, requested_rarity):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        num4 = 'SELECT * FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num4, (user_id,))
        pokemons = await cur.fetchone()

        if pokemons is None:
            return "You haven't caught any Pokémon yet."

        pokebols = f'Your {requested_rarity} rarity pokemons:\nPokebols: {pokemons[2]}'
        text = '\n'.join((pokebols, "\n".join(f'{pokemon_name}: {poke_count}' for poke_count, pokemon_name in zip(pokemons[3:],
                                                                                                                  POKEMON_LIST) if poke_count > 0 and pokemon_name in RARITY_DICT[requested_rarity])))

    return text

async def add_pokebols(user_id, amount):
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        update_query = "UPDATE number_of_pokemons SET pokebols = pokebols + ? WHERE user_id = ?"
        await cur.execute(update_query, (amount, user_id))

async def pokebols_number(user_id):
    number = 0
    async with AsyncDatabaseConnection('pokedex.sql') as cur:
        num5 = 'SELECT pokebols FROM number_of_pokemons WHERE user_id = ?'
        await cur.execute(num5, (user_id,))
        result = await cur.fetchone()
        if result:
            number = int(result[0])
    return number



#проверяет последнюю дату запроса юзера на получение покеболов, и если это новый день, дает разрешение и перезаписывает дату
async def check_pokebols_elegibility(user_id):
    async with AsyncDatabaseConnection('pokedex.sql') as cursor:  # cursor уже является курсором
        await cursor.execute('SELECT last_access_date FROM number_of_pokemons WHERE user_id = ?', (user_id,))
        date_result = await cursor.fetchone()
        if date_result:
            date = date_result[0]
            now = datetime.now()
            current_date = now.strftime("%d/%m/%y")
            if date != current_date:
                await cursor.execute("UPDATE number_of_pokemons SET last_access_date = ? WHERE user_id = ?", (current_date, user_id))
                return True
            else:
                return False
        else:
            return False

def time_until_next_midnight():
    current_time = datetime.now()
    next_midnight = datetime(current_time.year, current_time.month, current_time.day) + timedelta(days=1)
    time_remaining = next_midnight - current_time
    hours, remainder = divmod(time_remaining.seconds, 3600)
    minutes = remainder // 60
    return f'{hours} часов, {minutes+1} минут'


async def main():
    # print(show_pokedex(668210174))
    # print(time_until_next_midnight())
    a = "mivtpox_pokedex"
    print(a.rstrip("_pokedx"))

if __name__ == "__main__":
    asyncio.run(main())










