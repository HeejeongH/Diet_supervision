from typing import List, Dict

class Ingredient:
    def __init__(self, name: str, price: float, amount_g: float):
        self.name = name
        self.price = price
        self.amount_g = amount_g

class Menu:
    def __init__(self, name: str, nutrients: Dict[str, float], ingredients: List[Ingredient], category: str):
        self.name = name
        self.nutrients = nutrients
        self.ingredients = ingredients
        self.category = category

class Meal:
    def __init__(self, menus: List[Menu], date: str, meal_type: str):
        self.menus = menus
        self.date = date
        self.meal_type = meal_type

class Diet:
    def __init__(self, meals: List[Meal]):
        self.meals = meals

class WeeklyDiet:
    def __init__(self, diets: List[Diet]):
        self.diets = diets

class NutrientConstraints:
    def __init__(self, min_values: Dict[str, float], max_values: Dict[str, float], weights: Dict[str, float]):
        self.min_values = min_values
        self.max_values = max_values
        self.weights = weights