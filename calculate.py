from calculation_types import RecipeResult, PriceKey, PriceResult


def calculate_price_of_recipe(recipe, purchase_location, crafting_location, sale_location, all_prices, location_data, distance_data, crafting_bonuses):
    cost = 0
    craft_info = 'BUY '
    formula = '('

    crafting_bonus = 1.18
    if recipe.category in location_data[crafting_location]:
        crafting_bonus = location_data[crafting_location][recipe.category]

    if recipe.category in crafting_bonuses:
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

    craft_info += f'-> CRAFT {recipe.result} at {crafting_location} with bonus {crafting_bonus:.2f} '

    result_price_key = PriceKey(recipe.result, sale_location)
    if result_price_key not in all_prices:
        return None

    print(recipe.result, crafting_location, all_prices[result_price_key], crafting_bonus, cost)

    distance_mod = 4 + distance_data[purchase_location][crafting_location] + distance_data[crafting_location][sale_location]

    profit = ((all_prices[result_price_key] * crafting_bonus) - cost)
    weight = ((all_prices[result_price_key] * crafting_bonus) / cost) * profit / distance_mod

    craft_info += f'-> SELL at {sale_location} for {all_prices[result_price_key]} :: formula: '

    formula = f'{all_prices[result_price_key]} * {crafting_bonus} - {formula} = {profit:.1f}'

    return RecipeResult(recipe,
                        purchase_location, crafting_location, sale_location,
                        profit,
                        weight,
                        craft_info + formula)
