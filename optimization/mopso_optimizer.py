import os
import yaml
from tqdm import tqdm
from random import uniform
from evaluation.evaluation import evaluate_pipeline
from optimization.objectives import MemoizedObjective, replaces_best, seed_all
import csv

def load_config(path="optimization/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def sample_particle(bounds):
    return {k: round(uniform(*v), 3) for k, v in bounds.items()}

def quantize_config(config, allowed_values):
    quantized = {}
    for key, value in config.items():
        values = allowed_values.get(key)
        if values:
            quantized[key] = min(values, key=lambda x: abs(x - value))
        else:
            quantized[key] = value
    return quantized

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

def run_mopso(bounds, allowed_values, num_particles=20, generations=50, log_path="results/mopso_log.csv", video_path="sample_videos/mot20-05sample.mp4", embedder="mobilenet", device=None, seed=None, objective=None):
    if seed is not None:
        seed_all(seed)

    if objective is None:
        def objective(config):
            mota, idf1, fps = evaluate_pipeline(
                config, video_path=video_path, embedder=embedder, device=device
            )
            log_to_csv(config, mota, idf1, fps, log_path)
            return mota, idf1, fps
    obj = MemoizedObjective(objective)

    particles = [sample_particle(bounds) for _ in range(num_particles)]
    velocities = [{k: 0.0 for k in bounds} for _ in range(num_particles)]
    personal_best = list(particles)
    personal_best_score = [None] * num_particles  # cached — never re-evaluated
    global_best = None
    global_best_score = None  # (MOTA, IDF1, FPS), all maximized

    for gen in range(generations):
        print(f"\n[MOPSO] Generation {gen + 1}/{generations}")
        for i in tqdm(range(num_particles)):
            config = quantize_config(particles[i], allowed_values)
            score = obj(config)  # memoized

            # Personal best update — compares against the cached score, no
            # second evaluation (was O(2·particles) per generation, audit H4)
            if replaces_best(score, personal_best_score[i]):
                personal_best[i] = particles[i]
                personal_best_score[i] = score

            # Global best update
            if replaces_best(score, global_best_score):
                global_best_score = score
                global_best = particles[i]

        # Velocity + position update
        for i in range(num_particles):
            for k in bounds:
                r1, r2 = uniform(0, 1), uniform(0, 1)
                cognitive = r1 * (personal_best[i][k] - particles[i][k])
                social = r2 * (global_best[k] - particles[i][k])
                velocities[i][k] = 0.5 * velocities[i][k] + cognitive + social
                particles[i][k] += velocities[i][k]
                particles[i][k] = round(max(bounds[k][0], min(bounds[k][1], particles[i][k])), 3)

    print("\n[✓] Best MOPSO Config Found:")
    print(global_best)
    print(f"Real evaluations: {obj.evaluations}")
    return global_best
