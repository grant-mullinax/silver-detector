import itertools

import util
from calculation_types import Strategy, PriceKey, PriceResult, CompoundStrategy
import multiprocessing
import functools
import operator

purchase_locations = {
    'Fort Sterling',
    'Bridgewatch',
    'Martlock',
    'Thetford',
    'Lymhurst',
    'Caerleon'
}

daily_crafting_bonuses = {
    'cursestaff',
    'mace'
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

location_distance_modifiers = {
    'Fort Sterling': {
        'Fort Sterling': 0,
        'Bridgewatch': 2,
        'Martlock': 2,
        'Thetford': 1,
        'Lymhurst': 1,
        'Caerleon': 4,
        'Black Market': 4,
    },
    'Bridgewatch': {
        'Fort Sterling': 2,
        'Bridgewatch': 0,
        'Martlock': 1,
        'Thetford': 2,
        'Lymhurst': 1,
        'Caerleon': 4,
        'Black Market': 4,
    },
    'Martlock': {
        'Fort Sterling': 2,
        'Bridgewatch': 1,
        'Martlock': 0,
        'Thetford': 1,
        'Lymhurst': 2,
        'Caerleon': 4,
        'Black Market': 4,
    },
    'Thetford': {
        'Fort Sterling': 1,
        'Bridgewatch': 2,
        'Martlock': 1,
        'Thetford': 0,
        'Lymhurst': 2,
        'Caerleon': 4,
        'Black Market': 4,
    },
    'Lymhurst': {
        'Fort Sterling': 1,
        'Bridgewatch': 1,
        'Martlock': 2,
        'Thetford': 2,
        'Lymhurst': 0,
        'Caerleon': 4,
        'Black Market': 4,
    },
    'Caerleon': {
        'Fort Sterling': 4,
        'Bridgewatch': 4,
        'Martlock': 4,
        'Thetford': 4,
        'Lymhurst': 4,
        'Caerleon': 0,
        'Black Market': 0,
    },
}


def calculate_money(prices, recipes):
    results = []
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    loading_limit = len(purchase_locations) * len(crafting_locations) * len(sale_locations)
    loading_count = 0
    for purchase_location in purchase_locations:
        for crafting_location in crafting_locations:
            for sale_location in sale_locations:
                if loading_count % 3 == 0:
                    print(f"Calculating... {loading_count / loading_limit * 100:.0f}/100", end='\r')
                results += map(functools.partial(calculate_price_of_strategy,
                                                 purchase_location=purchase_location,
                                                 crafting_location=crafting_location,
                                                 sale_location=sale_location,
                                                 all_prices=prices), recipes)
                loading_count += 1

    return list(filter(functools.partial(operator.is_not, None), results))


def calculate_price_of_strategy(recipe, purchase_location, crafting_location, sale_location, all_prices):
    cost = 0
    craft_info = 'BUY '
    formula = '('

    crafting_bonus = 1.18
    if recipe.category in crafting_locations[crafting_location]:
        crafting_bonus = crafting_locations[crafting_location][recipe.category]

    if recipe.category in daily_crafting_bonuses:
        crafting_bonus += 0.1

    for ingredient in recipe.ingredients:
        price_key = PriceKey(ingredient.name, purchase_location)

        # we can also buy where we craft
        alt_price_key = PriceKey(ingredient.name, crafting_location)

        if price_key not in all_prices:
            return None

        # we arent guarding against 0.. but there should be none.
        if alt_price_key in all_prices and all_prices[alt_price_key] < all_prices[price_key]:
            price_result = all_prices[alt_price_key]
            craft_info += f'{alt_price_key.name} at {alt_price_key.city}, '
        else:
            price_result = all_prices[price_key]
            craft_info += f'{price_key.name} at {price_key.city}, '

        if not ingredient.no_bonus:
            cost += price_result * ingredient.count
            formula += f'{ingredient.count}*{price_result} + '
        else:
            cost += price_result * ingredient.count * crafting_bonus
            formula += f'{ingredient.count}*{price_result}*{crafting_bonus} + '

    formula = formula[:-3] + ')'

    if recipe.silver_cost is not None or recipe.silver_cost == 0:
        cost += recipe.silver_cost * crafting_bonus
        formula += f' - {recipe.silver_cost}'

    craft_info += f'-> CRAFT {recipe.result} at {crafting_location} with bonus {crafting_bonus:.2f} '

    result_price_key = PriceKey(recipe.result, sale_location)
    if result_price_key not in all_prices:
        return None

    distance_mod = 1 + location_distance_modifiers[purchase_location][crafting_location] + \
                   location_distance_modifiers[crafting_location][sale_location]

    profit = ((all_prices[result_price_key] * crafting_bonus) - cost) * 0.935
    weight = ((all_prices[result_price_key] * crafting_bonus) / cost) / distance_mod * profit

    craft_info += f'-> SELL at {sale_location} for {all_prices[result_price_key]} :: formula: '

    formula = f'{all_prices[result_price_key]} * .0.935 * {crafting_bonus} - {formula} = {profit:.1f}'

    return Strategy(recipe,
                    purchase_location, crafting_location, sale_location,
                    profit,
                    weight,
                    craft_info + formula)


def calculate_compound_strategies(strategies):
    compound_strategies = []

    strategies_by_result = {}

    for strategy in strategies:
        if strategy.recipe.result not in strategies_by_result:
            strategies_by_result[strategy.recipe.result] = []

        if strategy.sale_location == 'Black Market':
            continue
        strategies_by_result[strategy.recipe.result].append(strategy)

    total_strategies = len(strategies)
    loading_count = 0
    for strategy in strategies:
        strategies_per_ingredient = {}
        for ingredient in strategy.recipe.ingredients:
            if ingredient.name in strategies_by_result:
                # for every strategy we can simply just buy the item
                strategies_per_ingredient[ingredient.name] = strategies_by_result[ingredient.name] + [None]
            else:
                strategies_per_ingredient[ingredient.name] = [None]

        strategies_product = util.dict_product(strategies_per_ingredient)

        for ingredient_ordering in itertools.permutations(strategy.recipe.ingredients):
            for strategy_product in strategies_product:
                weight_sum = 0
                profit_sum = 0

                substrategies = []

                # filter out nones because we are just buying those directly with no substrategy
                none_filtered_ingredient_ordering = []

                for ingredient in ingredient_ordering:
                    strategy_for_ingredient = strategy_product[ingredient.name]
                    if strategy_for_ingredient is None:
                        continue

                    substrategies.append(strategy_for_ingredient)
                    weight_sum += strategy_for_ingredient.weight * ingredient.count
                    profit_sum += strategy_for_ingredient.profit * ingredient.count

                    none_filtered_ingredient_ordering.append(ingredient)

                # add the final craft after all the substrategies
                substrategies.append(strategy)
                weight_sum += strategy.weight
                profit_sum += strategy.profit

                distance_mod = 1
                for ingredient_index in range(len(none_filtered_ingredient_ordering) - 1):
                    from_strategy = strategy_product[none_filtered_ingredient_ordering[ingredient_index].name]
                    to_strategy = strategy_product[none_filtered_ingredient_ordering[ingredient_index + 1].name]
                    distance_mod += location_distance_modifiers[from_strategy.sale_location][to_strategy.purchase_location]

                if len(none_filtered_ingredient_ordering) > 0:
                    final_substrategy = strategy_product[none_filtered_ingredient_ordering[-1].name]
                    distance_mod += location_distance_modifiers[final_substrategy.sale_location][strategy.purchase_location]

                compound_strategies.append(CompoundStrategy(substrategies, profit_sum, weight_sum, "xd"))

        loading_count += 1
        print(f"Calculating compound strategies... {loading_count}/{total_strategies}", end='\r')

    return compound_strategies






