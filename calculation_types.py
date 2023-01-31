from collections import namedtuple

Recipe = namedtuple('Recipe', 'ingredients result focus category')
Ingredient = namedtuple('Ingredient', 'name count no_bonus')
PriceKey = namedtuple('PriceKey', 'name city')
PriceResult = namedtuple('PriceResult', 'price sold')
RecipeResult = namedtuple('RecipeResult', 'recipe purchase_location crafting_location sale_location profit weight '
                                          'calculation_data')