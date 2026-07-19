import matplotlib.pyplot as plt
import csv
import os


def load_results(csv_path):
    mota_list, idf1_list, fps_list = [], [], []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mota_list.append(float(row["MOTA"]))
            idf1_list.append(float(row["IDF1"]))
            fps_list.append(float(row["FPS"]))
    return mota_list, idf1_list, fps_list


def plot_pareto_3d(mota, idf1, fps, save_path="results/pareto_3d.png", show=True):
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(fps, mota, idf1, c="r", marker="o")
    ax.set_xlabel("FPS (↑)")
    ax.set_ylabel("MOTA (↑)")
    ax.set_zlabel("IDF1 (↑)")
    ax.set_title("3D Pareto Front")
    plt.tight_layout()
    plt.savefig(save_path)
    if show:
        plt.show()
    plt.close()


def plot_pareto_2d(mota, fps, save_path="results/pareto_2d.png", show=True):
    plt.figure()
    plt.scatter(fps, mota, c="b", label="MOTA vs FPS")
    plt.xlabel("FPS (↑)")
    plt.ylabel("MOTA (↑)")
    plt.title("2D Pareto Front")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path)
    if show:
        plt.show()
    plt.close()


if __name__ == "__main__":
    csv_path = "results/optimization_log.csv"
    if not os.path.exists(csv_path):
        print(f"[!] CSV file not found: {csv_path}")
        exit(1)

    mota, idf1, fps = load_results(csv_path)
    plot_pareto_3d(mota, idf1, fps)
    plot_pareto_2d(mota, fps)
