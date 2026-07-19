# run_plot_pareto.py

from nsga_optimization import run_nsga
from plot_pareto import plot_pareto

if __name__ == "__main__":
    # 1. Run the NSGA-II optimization
    pop, log, hof = run_nsga(generations=10, pop_size=20)

    # 2. Visualize the results
    plot_pareto(pop)
