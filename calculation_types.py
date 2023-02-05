from collections import namedtuple

Recipe = namedtuple('Recipe', 'ingredients result silver_cost focus category')
Ingredient = namedtuple('Ingredient', 'name count no_bonus')
PriceKey = namedtuple('PriceKey', 'name city')
PriceResult = namedtuple('PriceResult', 'price sold')
Strategy = namedtuple('Strategy', 'recipe location cost revenue calculation_data')
CompoundStrategy = namedtuple('CompoundStrategy', 'substrategies cost revenue profit weight calculation_data')
