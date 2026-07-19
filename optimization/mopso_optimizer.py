import os
import yaml
import numpy as np
from tqdm import tqdm
from random import uniform
from evaluation.evaluation import evaluate_pipeline
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

def run_mopso(bounds, allowed_values, num_particles=20, generations=50, log_path="results/mopso_log.csv", video_path="sample_videos/mot20-05sample.mp4"):
    particles = [sample_particle(bounds) for _ in range(num_particles)]
    velocities = [{k: 0.0 for k in bounds} for _ in range(num_particles)]
    personal_best = list(particles)
    global_best = None
    global_best_score = (-1, -1, float('inf'))  # MOTA, IDF1, 1/FPS

    for gen in range(generations):
        print(f"\n[MOPSO] Generation {gen + 1}/{generations}")
        for i in tqdm(range(num_particles)):
            config = quantize_config(particles[i], allowed_values)
            mota, idf1, fps = evaluate_pipeline(config, video_path=video_path)
            score = (mota, idf1, 1 / max(fps, 1e-3))
            log_to_csv(config, mota, idf1, fps, log_path)

            # Personal best update
            p_config = quantize_config(personal_best[i], allowed_values)
            p_mota, p_idf1, p_fps = evaluate_pipeline(p_config, video_path=video_path)
            p_score = (p_mota, p_idf1, 1 / max(p_fps, 1e-3))
            if score > p_score:
                personal_best[i] = particles[i]

            # Global best update
            if score > global_best_score:
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
    return global_best
