# Simulation-and-Path-Optimization-of-Warehouse-Order-Picking-Systems
A SimPy-based discrete-event simulation framework for warehouse order picking systems, comparing multiple path-planning strategies and picking modes.

## Project Structure

```
仓储订单拣选系统仿真与路径优化/
├── src/                              # Core source code
│   ├── config.py                     # Global configuration parameters
│   ├── warehouse.py                  # Warehouse model (parallel-aisle, ABC layout)
│   ├── order_gen.py                  # Order generator (Poisson arrivals, ABC-weighted)
│   ├── simulation.py                 # SimPy simulation engine (single-order mode)
│   ├── experiment.py                 # Batch experiment framework (full factorial)
│   ├── visualize.py                  # Visualization module (box/line/bar charts)
│   └── algorithms/                   # Path planning strategies
│       ├── s_shape.py                # S-Shape traversal strategy (baseline)
│       ├── largest_gap.py            # Largest Gap heuristic
│       ├── genetic.py                # Genetic Algorithm (GA)
│       ├── hybrid_ga.py              # Hybrid GA (HSGA, LG-seeded population)
│       └── batch_picking.py          # Batch picking simulation engine
├── scripts/                          # Runners and utilities
│   ├── run_productivity_experiment.py  # Experiment 1: strategy comparison
│   ├── run_scale_experiment.py         # Experiment 2: scale sensitivity
│   ├── run_batch_experiment.py         # Experiment 3: batch picking
│   ├── run_all_experiments.py          # Run all + generate plots
│   ├── generate_plots.py               # CSV → PNG charts
│   ├── generate_report.py              # Generate experiment report (.docx)
│   └── draw_layout.py                  # Draw warehouse layout diagram
├── results/                          # Experiment outputs (CSV, PNG, DOCX)
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── .gitignore
```

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Experiments

```bash
# Individual experiments
python scripts/run_productivity_experiment.py   # Exp 1: 120 simulations
python scripts/run_scale_experiment.py          # Exp 2: 45 simulations
python scripts/run_batch_experiment.py          # Exp 3: 90 simulations

# Or run everything at once (with plots)
python scripts/run_all_experiments.py           # 255 simulations
```

### Generate Visualizations

```bash
# Generate charts from existing CSV data
python scripts/generate_plots.py
```

### Generate the Report

```bash
# After running experiments to produce CSV data
python scripts/draw_layout.py        # Generate warehouse layout diagram
python scripts/generate_report.py    # Generate full experiment report (.docx)
```

## Experiment Design

### Experiment 1: Strategy Productivity Comparison
- **Strategies**: S-Shape, Largest Gap, GA, HSGA (4 total)
- **Factors**: arrival rate (180s / 300s / 600s) × pickers (1 / 2)
- **Size**: 4 × 3 × 2 × 5 = 120 simulations

### Experiment 2: Warehouse Scale Sensitivity
- **Strategies**: S-Shape, Largest Gap, HSGA (3 total)
- **Factors**: number of aisles (5 / 10 / 20)
- **Size**: 3 × 3 × 5 = 45 simulations

### Experiment 3: Batch Picking Comparison
- **Modes**: single-order picking vs batch picking (both using LG internally)
- **Factors**: arrival rate (180s / 300s / 600s) × batch window (120s / 300s / 600s)
- **Size**: 2 × 3 × 3 × 5 = 90 simulations

## System Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Warehouse layout | 10 aisles × 20 positions | Rectangular parallel-aisle |
| Total SKUs | 400 | ABC classification (A:B:C = 20%:30%:50%) |
| Aisle spacing | 2.5 m | Center-to-center |
| Position spacing | 1.0 m | Within-aisle |
| Walking speed | 1.0 m/s | Constant velocity |
| Pick time | 3.0 s/item | Per pick operation |
| Simulation duration | 8 hours | Including 1-hour warmup |
| GA parameters | 30 gen × 20 pop | Reduced config for experiments |

## Key Findings

| Finding | Key Data |
|---------|----------|
| Largest Gap is the best single-order strategy | Distance −11.4%, flow time −26.6% |
| HSGA validates heuristic population seeding | GA −2.4% → HSGA −5.0% (+108% gain) |
| Batch picking dramatically reduces per-order distance | 123.0 m → 88.9 m (−27.7%) |
| Distance decouples from system load | Distance variation < 3.5% across arrival rates |

## Dependencies

- Python ≥ 3.10
- simpy ≥ 4.0
- numpy ≥ 1.24
- matplotlib ≥ 3.5
- deap ≥ 1.3
- python-docx ≥ 0.8

## License

For academic research and educational use only.
