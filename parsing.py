from datetime import date, timedelta

from calculation_types import PriceKey, Ingredient, Recipe


def find_enchantment_suffix_for_json(tree):
    if '@enchantmentlevel' not in tree:
        return ''

    enchantment_level = tree['@enchantmentlevel']
    if int(enchantment_level) == 0:
        enchantment_suffix = ''
    else:
        enchantment_suffix = '@' + enchantment_level

    return enchantment_suffix


def parse_crafting_requirements(craft_data, item_data):
    crafting_requirements = craft_data['craftingrequirements']
    if type(crafting_requirements) is dict:
        crafting_requirements = [crafting_requirements]

    recipes = []
    for crafting_requirement in crafting_requirements:
        if '@uniquename' in craft_data:
            item_name = craft_data['@uniquename']
        else:
            item_name = item_data['@uniquename']

        if '@silver' in crafting_requirement:
            silver_cost = int(crafting_requirement['@silver'])
        else:
            silver_cost = None
        recipe = Recipe([],
                        item_name + find_enchantment_suffix_for_json(craft_data),
                        silver_cost,
                        crafting_requirement.get('@craftingfocus'),
                        item_data.get('@craftingcategory'))

        if 'craftresource' not in crafting_requirement:
            continue
        craft_resource = crafting_requirement['craftresource']

        if type(craft_resource) is dict:
            craft_resource = [craft_resource]

        for resource in craft_resource:
            # if 'rune' in resource['@uniquename']:

            recipe.ingredients.append(
                Ingredient(resource['@uniquename'] + find_enchantment_suffix_for_json(resource),
                           int(resource['@count']),
                           '@maxreturnamount' in resource))

        recipes.append(recipe)

    return recipes


def parse_recipes(item_data):
    recipes = []
    for item in item_data:
        if 'craftingrequirements' not in item:
            continue
        recipes += parse_crafting_requirements(item, item)

        if 'enchantments' in item:
            for enchantment in item['enchantments']['enchantment']:
                recipes += parse_crafting_requirements(enchantment, item)
    return recipes


def parse_price_data(price_data):
    prices = {}
    for price in price_data:
        if price['sell_price_min'] == 0:
            continue
        parsed_location = price['city']
        if parsed_location.endswith(" Portal"):
            parsed_location = parsed_location[:-len(" Portal")]

        price_key = PriceKey(price['item_id'], parsed_location)

        if price_key not in prices or price['sell_price_min'] < prices[price_key]:
            prices[price_key] = price['sell_price_min']

    return prices


def parse_history_data(price_data):
    prices = {}
    for price in price_data:
        if len(price['data']) > 0:

            sold_sum = 0
            price_sum = 0
            for entry in price['data']:
                sold_sum += entry['item_count']
                price_sum += entry['avg_price']

            if sold_sum > 1400:
                parsed_location = price['location']
                if parsed_location.endswith(" Portal"):
                    parsed_location = parsed_location[:-len(" Portal")]

                prices[PriceKey(price['item_id'], parsed_location)] = price_sum / len(price['data'])

    return prices


# get price and history, then merge
def get_all_price_data(items, session):
    prices = {}
    start_date = (date.today() - timedelta(days=14)).strftime('%m-%d-%Y')
    end_date = date.today().strftime('%m-%d-%Y')

    # make calls for all unique ingredients to get price
    remaining_unique_ingredients = list(items)
    remaining_unique_ingredients.sort()

    ingredient_count = len(remaining_unique_ingredients)

    while len(remaining_unique_ingredients) > 0:
        # make the url
        item_string = ''
        while len(item_string) < 1800 and len(remaining_unique_ingredients) > 0:
            item_string += remaining_unique_ingredients.pop() + ','

        prices_response = session.get(f'https://www.albion-online-data.com/api/v2/stats/prices/{item_string}.json')
        history_response = session.get(f'https://www.albion-online-data.com/api/v2/stats/history/{item_string}'
                                       f'?date={start_date}&end_date={end_date}&time-scale=24')

        # merge price into history data. if its not in history then ignore it because it probably never sells
        price_data = parse_price_data(prices_response.json())
        history_data = parse_history_data(history_response.json())

        filtered_data = {}

        for entry, price_value in price_data.items():
            if entry in history_data and history_data[entry] * 0.6 < price_value < history_data[entry] * 1.4:
                filtered_data[entry] = price_value

        prices.update(filtered_data)

        num_remaining_unique_ingredients = ingredient_count - len(remaining_unique_ingredients)
        print(f"Pulling price data... {num_remaining_unique_ingredients}/{ingredient_count}", end='\r')

    print('')
    return prices
