from Diet_class import Menu, Meal, Diet, NutrientConstraints
from typing import List, Union, Dict
import numpy as np
from evaluation_function import evaluate_nutrition, evaluate_cost, evaluate_harmony, evaluate_diversity

class MultiObjectiveDietOptimizer:
    def __init__(self, all_menus: List[Menu], nutrient_constraints: NutrientConstraints, harmony_matrix: np.ndarray):
        self.all_menus = all_menus
        self.nutrient_constraints = nutrient_constraints
        self.harmony_matrix = harmony_matrix
        
    def fitness(self, diet_db: Diet, weeklydiet: Diet) -> List[float]:
        nutrition_score = evaluate_nutrition(weeklydiet, self.nutrient_constraints)
        cost_score = evaluate_cost(diet_db, weeklydiet)
        harmony_score = evaluate_harmony(diet_db, weeklydiet)
        diversity_score = evaluate_diversity(weeklydiet)
        
        return [nutrition_score, cost_score, harmony_score, diversity_score]

    def dominates(self, a: List[float], b: List[float]) -> bool:
        return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))

    def non_dominated_sort(self, population: List[Diet], fitnesses: List[List[float]]) -> List[List[int]]:
        n = len(population)
        domination_counts = [0] * n
        dominated_solutions = [[] for _ in range(n)]
        fronts = [[]]

        for i in range(n):
            for j in range(i+1, n):
                if self.dominates(fitnesses[i], fitnesses[j]):
                    dominated_solutions[i].append(j)
                    domination_counts[j] += 1
                elif self.dominates(fitnesses[j], fitnesses[i]):
                    dominated_solutions[j].append(i)
                    domination_counts[i] += 1
            
            if domination_counts[i] == 0:
                fronts[0].append(i)

        i = 0
        while fronts[i]:
            next_front = []
            for j in fronts[i]:
                for k in dominated_solutions[j]:
                    domination_counts[k] -= 1
                    if domination_counts[k] == 0:
                        next_front.append(k)
            i += 1
            fronts.append(next_front)

        return fronts[:-1]  # 마지막 빈 프론트 제거

    def crowding_distance(self, fitnesses: List[List[float]]) -> List[float]:
        n = len(fitnesses)
        distances = [0.0] * n
        for i in range(len(fitnesses[0])):
            sorted_indices = sorted(range(n), key=lambda k: fitnesses[k][i])
            distances[sorted_indices[0]] = distances[sorted_indices[-1]] = float('inf')
            if fitnesses[sorted_indices[-1]][i] == fitnesses[sorted_indices[0]][i]:
                continue
            norm = fitnesses[sorted_indices[-1]][i] - fitnesses[sorted_indices[0]][i]
            for j in range(1, n-1):
                distances[sorted_indices[j]] += (fitnesses[sorted_indices[j+1]][i] - fitnesses[sorted_indices[j-1]][i]) / norm

        return distances

    def selection(self, population: List[Diet], fitnesses: List[List[float]]) -> List[Diet]:
        fronts = self.non_dominated_sort(population, fitnesses)
        selected = []
        for front in fronts:
            if len(selected) + len(front) <= len(population) // 2:
                selected.extend(front)
            else:
                crowding_distances = self.crowding_distance([fitnesses[i] for i in front])
                sorted_front = sorted(front, key=lambda i: crowding_distances[front.index(i)], reverse=True)
                selected.extend(sorted_front[:len(population) // 2 - len(selected)])
                break
        return [population[i] for i in selected]

    def crossover(self, parent1: Diet, parent2: Diet) -> Diet:
        child_meals = []
        for meal1, meal2 in zip(parent1.meals, parent2.meals):
            child_menus = []
            for menu1, menu2 in zip(meal1.menus, meal2.menus):
                child_menus.append(menu1 if np.random.random() < 0.5 else menu2)
            child_meals.append(Meal(child_menus, meal1.date, meal1.meal_type))
        return Diet(child_meals)

    def mutate(self, diet: Diet) -> Diet:
        mutated_meals = []
        for meal in diet.meals:
            if np.random.random() < 0.1:  # 10% 확률로 변이
                mutated_menus = []
                for menu in meal.menus:
                    if np.random.random() < 0.5:  # 50% 확률로 메뉴 변경
                        new_menu = np.random.choice(self.all_menus)
                        mutated_menus.append(new_menu)
                    else:
                        mutated_menus.append(menu)
                mutated_meals.append(Meal(mutated_menus, meal.date, meal.meal_type))
            else:
                mutated_meals.append(meal)
        return Diet(mutated_meals)

    def optimize(self, diet_db: Diet, initial_diet: Diet, generations: int = 100, population_size: int = 50) -> List[Diet]:
        population = [initial_diet] + [self.mutate(initial_diet) for _ in range(population_size - 1)]
        initial_fitness = self.fitness(diet_db, initial_diet)
        
        for generation in range(generations):
            fitnesses = [self.fitness(diet_db, weeklydiet) for weeklydiet in population]
            
            # 비지배 정렬을 통해 파레토 프론트 찾기
            pareto_front_indices = self.non_dominated_sort(population, fitnesses)[0]
            pareto_front = [population[i] for i in pareto_front_indices]
            
            # 종료 조건 확인
            improved_diets = self.count_improved_diets(initial_fitness, pareto_front, diet_db)
            if improved_diets >= 5:
                print(f"Termination condition met at generation {generation}: {improved_diets} improved diets found.")
                return pareto_front
            
            parents = self.selection(population, fitnesses)
            
            offspring = []
            while len(offspring) < population_size - len(parents):
                if np.random.random() < 0.7:  # 70% 확률로 교차
                    child = self.crossover(*np.random.choice(parents, 2, replace=False))
                else:
                    child = self.mutate(np.random.choice(parents))
                offspring.append(child)
            
            population = parents + offspring
        
        print(f"Maximum generations reached. Best result so far: {len(pareto_front)} solutions in Pareto front.")
        return pareto_front

    def count_improved_diets(self, initial_fitness: List[float], pareto_front: List[Diet], diet_db: Diet) -> int:
        improved_count = 0
        for diet in pareto_front:
            current_fitness = self.fitness(diet_db, diet)
            improvements = sum(1 for init, curr in zip(initial_fitness, current_fitness) if curr > init)
            if improvements >= 3:
                improved_count += 1
        return improved_count