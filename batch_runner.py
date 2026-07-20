import os
import json
import csv
import torch
from evaluation.evaluation import evaluate_pipeline
from optimization.qpso_optimizer import qpso_optimize
from optimization.nsga_optimizer import run_nsga
from optimization.mopso_optimizer import run_mopso
from optimization.plot_pareto import plot_pareto_2d, plot_pareto_3d
import yaml

config_file = "optimization/config.yaml"
results_dir = "results"
summary_file = os.path.join(results_dir, "summary_table.csv")
video_path = "sample_videos/mot20-05sample.mp4"

# Real, installable deep_sort_realtime embedders (STORY-008). torchreid was
# dropped — it will not pip-install cleanly on Python 3.12 (unbounded native
# build-dep chain); revisit on the GPU box. CLIP weights auto-download on first
# use (gitignored).
embedders = ["mobilenet", "clip_ViT-B/32"]
optimizers = ["qpso", "nsga", "mopso"]

# Device stays config-driven (operator directive): env override wins, else
# auto-detect. Never hardcoded — this dev box is CPU, deployment is GPU.
DEVICE = os.environ.get("DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")


def load_config_space(path=config_file):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def flatten_config_space(config_space):
    if all(isinstance(v, list) for v in config_space.values()):
        bounds = {k: [min(v), max(v)] for k, v in config_space.items()}
        allowed = config_space
    else:
        bounds = {
            k: [min(v), max(v)]
            for section in config_space.values()
            for k, v in section.items()
        }
        allowed = {
            k: v for section in config_space.values() for k, v in section.items()
        }
    return bounds, allowed


def save_metrics(result, embedder, optimizer):
    folder = os.path.join(results_dir, embedder, optimizer)
    os.makedirs(folder, exist_ok=True)
    metrics_path = os.path.join(folder, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(result, f, indent=2)

    row = {
        "Embedder": embedder,
        "Optimizer": optimizer,
        "MOTA": result.get("MOTA", 0),
        "IDF1": result.get("IDF1", 0),
        "FPS": result.get("FPS", 0),
    }
    file_exists = os.path.exists(summary_file)
    with open(summary_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def plot_all(embedder, optimizer):
    path = os.path.join(results_dir, embedder, optimizer, "log.csv")
    if not os.path.exists(path):
        print(f"[!] Missing log.csv for {embedder} + {optimizer}")
        return
    try:
        mota_list, idf1_list, fps_list = [], [], []
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mota_list.append(float(row["MOTA"]))
                idf1_list.append(float(row["IDF1"]))
                fps_list.append(float(row["FPS"]))

        name_prefix = f"{embedder.replace('v2', '')}_{optimizer}".lower()
        plot_folder = os.path.join(results_dir, embedder, optimizer)
        plot_pareto_2d(
            mota_list,
            fps_list,
            save_path=os.path.join(plot_folder, f"{name_prefix}_2d.png"),
            show=False,
        )
        plot_pareto_3d(
            mota_list,
            idf1_list,
            fps_list,
            save_path=os.path.join(plot_folder, f"{name_prefix}_3d.png"),
            show=False,
        )
    except Exception as e:
        print(f"[!] Failed to plot {embedder} + {optimizer}: {e}")


def run_combo(embedder, optimizer):
    print(f"\n▶ Running {embedder} + {optimizer} on {DEVICE}...")

    config_space = load_config_space()
    bounds, allowed_values = flatten_config_space(config_space)

    log_path = os.path.join(results_dir, embedder, optimizer, "log.csv")

    if optimizer == "qpso":
        best_config = qpso_optimize(
            bounds, allowed_values, num_particles=20, generations=50, log_path=log_path,
            video_path=video_path, embedder=embedder, device=DEVICE,
        )
    elif optimizer == "nsga":
        best_config = run_nsga(
            bounds,
            allowed_values,
            num_individuals=20,
            generations=50,
            log_path=log_path,
            video_path=video_path,
            embedder=embedder,
            device=DEVICE,
        )
    elif optimizer == "mopso":
        best_config = run_mopso(
            bounds, allowed_values, num_particles=20, generations=50, log_path=log_path,
            video_path=video_path, embedder=embedder, device=DEVICE,
        )
    else:
        print(f"[✘] Unknown optimizer: {optimizer}")
        return

    if not isinstance(best_config, dict):
        print(
            f"[!] Optimizer '{optimizer}' for embedder '{embedder}' did not return a valid configuration. Skipping"
        )
        return

    mota, idf1, fps = evaluate_pipeline(
        best_config, device=DEVICE, video_path=video_path, embedder=embedder
    )
    result = {**best_config, "MOTA": mota, "IDF1": idf1, "FPS": fps}
    save_metrics(result, embedder, optimizer)
    plot_all(embedder, optimizer)


if __name__ == "__main__":
    for embedder in embedders:
        for optimizer in optimizers:
            run_combo(embedder, optimizer)

    print(f"\n[✓] Batch run complete. Summary saved to {summary_file}")
