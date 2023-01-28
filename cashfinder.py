import json
import itertools
import requests_cache
from datetime import date, timedelta
import multiprocessing
import functools
from calculate import calculate_price_of_recipe
from calculation_types import Recipe, Ingredient, PriceKey, PriceResult
import operator

if __name__ == '__main__':
    session = requests_cache.CachedSession('albion_data')

    # 1.18 is implicit
    locations = {
        'Fort Sterling': {
            'wood': 1.58,
            'hammer': 1.33,
            'spear': 1.33,
            'holystaff': 1.33,
            'plate_helmet': 1.33,
            'cloth_armor': 1.33,
        },
        'Bridgewatch': {
            'stone': 1.58,
            'crossbow': 1.33,
            'dagger': 1.33,
            'cursestaff': 1.33,
            'plate_armor': 1.33,
            'cloth_shoes': 1.33,
        },
        'Martlock': {
            'hide': 1.58,
            'axe': 1.33,
            'quarterstaff': 1.33,
            'froststaff': 1.33,
            'plate_shoes': 1.33,
            'offhand': 1.33,
        },
        'Lymhurst': {
            'fiber': 1.58,
            'axe': 1.33,
            'quarterstaff': 1.33,
            'froststaff': 1.33,
            'leather_helmet': 1.33,
            'leather_shoes': 1.33,
        },
        'Thetford': {
            'ore': 1.58,
            'mace': 1.33,
            'naturestaff': 1.33,
            'firestaff': 1.33,
            'leather_armor': 1.33,
            'cloth_helmet': 1.33,
        },
        'Caerleon': {
            'gatherergear': 1.33,
            'tool': 1.33,
            'food': 1.33,
            'firestaff': 1.33,
            'knuckles': 1.33,
        },
    }


    def parse_recipes(item_data):
        if 'craftingrequirements' not in item_data or '@craftingcategory' not in item_data:
            return []

        crafting_requirements = item_data['craftingrequirements']
        if type(crafting_requirements) is dict:
            crafting_requirements = [crafting_requirements]

        recipes = []
        for crafting_requirement in crafting_requirements:
            recipe = Recipe([], item_data['@uniquename'], crafting_requirement['@craftingfocus'],
                            item_data['@craftingcategory'])
            craft_resource = crafting_requirement['craftresource']

            if type(craft_resource) is dict:
                craft_resource = [craft_resource]

            for resource in craft_resource:
                recipe.ingredients.append(Ingredient(resource['@uniquename'], int(resource['@count'])))

            recipes.append(recipe)

        return recipes


    items_json = json.load(open('items.json'))

    target_items = items_json['items'][
        'weapon']  # + items_json['items']['simpleitem'] + items_json['items']['equipmentitem']

    # flatten
    all_recipes = list(itertools.chain(*[parse_recipes(weapon) for weapon in target_items]))

    unique_types = set()
    for weapon in target_items:
        if '@craftingcategory' in weapon:
            unique_types.add(weapon['@craftingcategory'])

    unique_ingredients = set()
    for recipe in all_recipes:
        unique_ingredients.add(recipe.result)
        for ingredient in recipe.ingredients:
            unique_ingredients.add(ingredient.name)


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


    def get_all_price_data():
        prices = {}
        start_date = (date.today() - timedelta(days=2)).strftime('%m-%d-%Y')
        end_date = date.today().strftime('%m-%d-%Y')

        # make calls for all unique ingredients to get price
        remaining_unique_ingredients = list(unique_ingredients)
        remaining_unique_ingredients.sort()
        while len(remaining_unique_ingredients) > 0:
            item_string = ''
            while len(item_string) < 1800 and len(remaining_unique_ingredients) > 0:
                item_string += ',' + remaining_unique_ingredients.pop()
            print("request!", item_string)
            response = session.get(f'https://www.albion-online-data.com/api/v2/stats/prices/{item_string}.json')
            prices.update(parse_price_data(response.json()))

        return prices


    all_prices = get_all_price_data()


    def calculate_money():
        results = []
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        for location in locations:
            results += map(functools.partial(calculate_price_of_recipe,
                                             location=location,
                                             all_prices=all_prices,
                                             location_data=locations), all_recipes)

        return list(filter(functools.partial(operator.is_not, None), results))


    r = sorted(calculate_money(), key=lambda x: x.profit, reverse=True)

    print('hi')
