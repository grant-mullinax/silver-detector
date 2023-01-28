from calculation_types import RecipeResult, PriceKey, PriceResult


def calculate_price_of_recipe(recipe, location, all_prices, location_data):
    cost = 0
    for ingredient in recipe.ingredients:
        price_key = PriceKey(ingredient.name, location)
        if price_key in all_prices:

            # guard against 0 values
            price_result = all_prices[price_key]
            if price_result == 0:
                return None
            cost += price_result * ingredient.count
        else:
            return None
    result_price_key = PriceKey(recipe.result, location)
    if result_price_key not in all_prices:
        return None

    crafting_bonus = 1.18
    if recipe.category in location_data:
        crafting_bonus = location_data[recipe.category]

    print(recipe.result, location, all_prices[result_price_key], crafting_bonus, cost)

    return RecipeResult(recipe,
                        location,
                        (all_prices[result_price_key] * crafting_bonus) / cost,
                        [recipe.result, location, all_prices[result_price_key], crafting_bonus, cost])
