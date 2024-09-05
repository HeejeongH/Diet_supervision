import pandas as pd

def diet_to_dataframe(diet, title: str) -> pd.DataFrame:
    meals_dict = {f'Day {i+1}': [] for i in range(7)}
    
    for i in range(7):
        day_meals = {
            'Breakfast': "",
            'Lunch': "",
            'Dinner': ""
        }
        for meal in diet.meals[i*3:(i+1)*3]: 
            menu_names = "\n".join([f"({menu.category}) {menu.name}" for menu in meal.menus])
            day_meals[meal.meal_type.capitalize()] = menu_names
        
        meals_dict[f'Day {i+1}'].extend([day_meals['Breakfast'], day_meals['Lunch'], day_meals['Dinner']])
    
    df = pd.DataFrame(meals_dict, index=['Breakfast', 'Lunch', 'Dinner'])
    df.columns.name = title 
    
    return df

def count_menu_changes(initial_diet, optimized_diet):
    changes = {}
    for initial_meal, optimized_meal in zip(initial_diet.meals, optimized_diet.meals):
        for initial_menu, optimized_menu in zip(initial_meal.menus, optimized_meal.menus):
            category = initial_menu.category
            if category not in changes:
                changes[category] = {'total': 0, 'changed': 0}
            changes[category]['total'] += 1
            if initial_menu.name != optimized_menu.name:
                changes[category]['changed'] += 1
    return changes