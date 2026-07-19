from deap import base, creator, tools, algorithms
import random
import numpy as np
import yaml
import os
import csv
from evaluation.evaluation import evaluate_pipeline

def load_config(path="optimization/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def make_individual(bounds):
    return [random.uniform(*bounds[key]) for key in bounds]

def decode_individual(ind, keys, allowed_values):
    return {key: min(allowed_values[key], key=lambda x: abs(x - ind[i])) for i, key in enumerate(keys)}

def log_to_csv(config, mota, idf1, fps, path):
    file_exists = os.path.exists(path)
    with open(path, 'a', newline='') as f:
        fieldnames = list(config.keys()) + ['MOTA', 'IDF1', 'FPS']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row = dict(config)
        row.update({'MOTA': mota, 'IDF1': idf1, 'FPS': fps})
        writer.writerow(row)

def run_nsga(bounds, allowed_values, num_individuals=20, generations=50, log_path="results/nsga_log.csv", video_path="sample_videos/mot20-05sample.mp4"):
    keys = list(bounds.keys())

    # Define DEAP toolbox
    creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0, -1.0))  # maximize MOTA, IDF1; minimize 1/FPS
    creator.create("Individual", list, fitness=creator.FitnessMulti)
    toolbox = base.Toolbox()
    toolbox.register("attr_float", make_individual, bounds)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.attr_float)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(ind):
        config = decode_individual(ind, keys, allowed_values)
        mota, idf1, fps = evaluate_pipeline(config, video_path=video_path)
        log_to_csv(config, mota, idf1, fps, log_path)
        return mota, idf1, 1 / max(fps, 1e-3)

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded,
                     low=[b[0] for b in bounds.values()],
                     up=[b[1] for b in bounds.values()], eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded,
                     low=[b[0] for b in bounds.values()],
                     up=[b[1] for b in bounds.values()], eta=20.0, indpb=0.2)
    toolbox.register("select", tools.selNSGA2)

    pop = toolbox.population(n=num_individuals)
    algorithms.eaMuPlusLambda(pop, toolbox,
                              mu=num_individuals,
                              lambda_=2*num_individuals,
                              cxpb=0.6,
                              mutpb=0.3,
                              ngen=generations,
                              stats=None,
                              halloffame=None,
                              verbose=True)

    best = tools.selBest(pop, 1)[0]
    best_config = decode_individual(best, keys, allowed_values)
    print("\n[✓] Best NSGA-II Config Found:")
    print(best_config)
    return best_config
