import json
import itertools
import requests_cache
from datetime import timedelta

from pyrate_limiter import RequestRate, Duration
from requests_ratelimiter import LimiterAdapter

from CachedLimiterSession import CachedLimiterSession
from calculate import calculate_money, calculate_compound_strategies
from calculation_types import Recipe, Ingredient, PriceKey
from parsing import parse_recipes, get_all_price_data

if __name__ == '__main__':
    rate_limit_adapter = LimiterAdapter(per_minute=100,
                                        burst=179)

    session = requests_cache.CachedSession(
        cache_name='albion_data',
        expire_after=timedelta(hours=4),
    )

    session.mount('https://www.albion-online-data.com/', adapter=rate_limit_adapter)

    items_json = json.load(open('items.json'))

    target_items = \
        items_json['items']['weapon'] + \
        items_json['items']['simpleitem']
    # items_json['items']['equipmentitem'] + \

    # flatten
    all_recipes = parse_recipes(target_items)

    unique_types = set()
    for weapon in target_items:
        if '@craftingcategory' in weapon:
            unique_types.add(weapon['@craftingcategory'])

    unique_ingredients = set()
    for recipe in all_recipes:
        unique_ingredients.add(recipe.result)
        for ingredient in recipe.ingredients:
            unique_ingredients.add(ingredient.name)

    # add no-craft transporting
    for ingredient in unique_ingredients:
        all_recipes.append(Recipe([Ingredient(ingredient, 1, True)], ingredient, None, 0, 'transport'))

    all_prices = get_all_price_data(unique_ingredients, session)

    best_crafts = calculate_money(all_prices, all_recipes)

    max_for_item = {}
    for result in best_crafts:
        price_key = PriceKey(result.recipe.result, result.sale_location)
        if (price_key not in max_for_item or result.weight > max_for_item[price_key].weight) and result.weight > 0:
            # if any(ingredient.name == 'T6_PLANKS_LEVEL2@2' or ingredient.name == 'T6_PLANKS_LEVEL3@3' for ingredient in result.recipe.ingredients):
            max_for_item[price_key] = result

    filtered_results = [entry for key, entry in max_for_item.items()]

    sorted_results = sorted(filtered_results, key=lambda x: x.weight, reverse=True)

    compound_strategies = calculate_compound_strategies(list(filter(lambda x: x.weight > 0, best_crafts)))

    sorted_compound_strategies = sorted(compound_strategies, key=lambda x: x.weight, reverse=True)

    for x in sorted_results[:100]:
        print(x.calculation_data)
    print('hi')
