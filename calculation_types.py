from collections import namedtuple

Recipe = namedtuple('Recipe', 'ingredients result focus category')
Ingredient = namedtuple('Ingredient', 'name count')
PriceKey = namedtuple('PriceKey', 'name city')
PriceResult = namedtuple('PriceResult', 'price sold')
RecipeResult = namedtuple('RecipeResult', 'recipe location profit')