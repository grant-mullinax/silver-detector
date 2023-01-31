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

    purchase_locations = {
        'Fort Sterling',
        'Bridgewatch',
        'Martlock',
        'Thetford',
        'Lymhurst',
        'Caerleon'
    }

    crafting_bonuses = {
        'plate_armor',
        'sword'
    }

    # 1.18 is implicit
    crafting_locations = {
        'Fort Sterling': {
            'wood': 1.58,
            'hammer': 1.59,
            'spear': 1.59,
            'holystaff': 1.59,
            'plate_helmet': 1.59,
            'cloth_armor': 1.59,
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
            'sword': 1.33,
            'bow': 1.33,
            'arcanestaff': 1.33,
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
        }
    }

    sale_locations = {
        'Fort Sterling',
        'Bridgewatch',
        'Martlock',
        'Thetford',
        'Lymhurst',
        'Caerleon',
        'Black Market'
    }

    distance_modifiers = {
         'Fort Sterling': {
             'Fort Sterling': 0,
             'Bridgewatch': 2,
             'Martlock': 2,
             'Thetford': 1,
             'Lymhurst': 1,
             'Caerleon': 3,
             'Black Market': 3,
         },
        'Bridgewatch': {
            'Fort Sterling': 2,
            'Bridgewatch': 0,
            'Martlock': 1,
            'Thetford': 2,
            'Lymhurst': 1,
            'Caerleon': 3,
            'Black Market': 3,
        },
        'Martlock': {
            'Fort Sterling': 2,
            'Bridgewatch': 1,
            'Martlock': 0,
            'Thetford': 1,
            'Lymhurst': 2,
            'Caerleon': 3,
            'Black Market': 3,
        },
        'Thetford': {
            'Fort Sterling': 1,
            'Bridgewatch': 2,
            'Martlock': 1,
            'Thetford': 0,
            'Lymhurst': 2,
            'Caerleon': 3,
            'Black Market': 3,
        },
        'Lymhurst': {
            'Fort Sterling': 1,
            'Bridgewatch': 1,
            'Martlock': 2,
            'Thetford': 2,
            'Lymhurst': 0,
            'Caerleon': 3,
            'Black Market': 3,
        },
        'Caerleon': {
            'Fort Sterling': 3,
            'Bridgewatch': 3,
            'Martlock': 3,
            'Thetford': 3,
            'Lymhurst': 3,
            'Caerleon': 0,
            'Black Market': 0,
        },
    }

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
            recipe = Recipe([], item_name + find_enchantment_suffix_for_json(craft_data),
                            crafting_requirement['@craftingfocus'],
                            item_data['@craftingcategory'])
            craft_resource = crafting_requirement['craftresource']

            if type(craft_resource) is dict:
                craft_resource = [craft_resource]

            for resource in craft_resource:
                recipe.ingredients.append(Ingredient(resource['@uniquename'] + find_enchantment_suffix_for_json(resource),
                                                     int(resource['@count']),
                                                     '@maxreturnamount' in resource))

            recipes.append(recipe)

        return recipes


    def parse_recipes(item_data):
        if '@craftingcategory' not in item_data or 'craftingrequirements' not in item_data:
            return []
        recipes = parse_crafting_requirements(item_data, item_data)

        if 'enchantments' in item_data:
            for enchantment in item_data['enchantments']['enchantment']:
                recipes += parse_crafting_requirements(enchantment, item_data)

        return recipes


    items_json = json.load(open('items.json'))

    target_items = items_json['items']['weapon'] + items_json['items']['equipmentitem'] # + items_json['items']['simpleitem']

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
    def get_all_price_data(items):
        prices = {}
        start_date = (date.today() - timedelta(days=14)).strftime('%m-%d-%Y')
        end_date = date.today().strftime('%m-%d-%Y')

        # make calls for all unique ingredients to get price
        remaining_unique_ingredients = list(items)
        remaining_unique_ingredients.sort()

        while len(remaining_unique_ingredients) > 0:

            # make the url
            item_string = ''
            while len(item_string) < 1800 and len(remaining_unique_ingredients) > 0:
                item_string += ',' + remaining_unique_ingredients.pop()
            print("request!", item_string)

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

        return prices

    # add no-craft transporting
    # for ingredient in unique_ingredients:
    #    all_recipes.append(Recipe([Ingredient(ingredient, 1, True)], ingredient, 0, 'transport'))

    all_prices = get_all_price_data(unique_ingredients)


    def calculate_money():
        results = []
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        for purchase_location in purchase_locations:
            for crafting_location in crafting_locations:
                for sale_location in sale_locations:
                    results += map(functools.partial(calculate_price_of_recipe,
                                                     purchase_location=purchase_location,
                                                     crafting_location=crafting_location,
                                                     sale_location=sale_location,
                                                     all_prices=all_prices,
                                                     location_data=crafting_locations,
                                                     distance_data=distance_modifiers,
                                                     crafting_bonuses=crafting_bonuses), all_recipes)

        return list(filter(functools.partial(operator.is_not, None), results))

    best_crafts = calculate_money()

    max_for_item = {}
    for result in best_crafts:
        if result.recipe.result not in max_for_item or result.weight > max_for_item[result.recipe.result].weight:
            # if any(ingredient.name == 'T6_PLANKS_LEVEL2@2' or ingredient.name == 'T6_PLANKS_LEVEL3@3' for ingredient in result.recipe.ingredients):
            max_for_item[result.recipe.result] = result

    filtered_results = [entry for key, entry in max_for_item.items()]

    r = sorted(filtered_results, key=lambda x: x.weight, reverse=True)

    for x in r[:100]:
        print(x.calculation_data)
    print('hi')
