# NYC Subway Optimization Project

**Graph Construction • Data Preprocessing • Gurobi Optimization Model**

This repository contains all code used to build a multi-line subway network graph for the NYC Subway, preprocess ridership and GTFS datasets, and run a system-wide train frequency optimization model using **Gurobi**. The project focuses on weekday rush-hour demand and evaluates optimized train allocations against the published MTA schedule.

---

## Project Overview

This project optimizes train frequencies and route allocations across the NYC Subway during weekday rush hours. The pipeline consists of three major components:

### **1. Subway Graph Construction**

* Parses GTFS (`trips.txt`, `stop_times.txt`, `stops.txt`, `routes.txt`, `transfers.txt`).
* Builds a **directed multi-graph** where edges may belong to multiple subway lines.
* Merges stations with multiple complex IDs by leveraging GTFS transfer metadata.
* Computes traversal times between stations.
* Outputs a `networkx` multi-digraph used by the optimizer.

### **2. Data Preprocessing**

* Loads hourly ridership data from NYC Open Data (2020–2024).
* Extracts:

  * **6–10am entries** (AM peak inbound flows)
  * **4–8pm exits** (PM peak outbound flows)
* Normalizes and integerizes demand while preserving realistic network proportions.
* Maps ridership entries to graph stations.
* Prepares capacity, line lengths, and route-specific metadata.

### **3. Gurobi Optimization Model**

Implements the final model that assigns hourly train frequencies to each subway line, subject to:

* Line-specific capacity constraints
* Minimum train frequency constraints
* Demand satisfaction via multi-line flows (`x_{i,j,l}`)
* Train energy / operational cost approximation
* Objective that minimizes system-wide travel time and operational cost

The notebook in `model.ipynb` demonstrates the full optimization pipeline.

---

## Reproducibility

### **Install Requirements**

```bash
pip install networkx matplotlib cartopy
```

### **Run Graph Construction**

```bash
python GTFS_MTA_with_routes.py
```

### **Run Preprocessing**

```bash
python aggregate_turnstile_data.py
python map_turnstile_data_to_gtfs_id.py
python create_nodes_with_ridership_info.py
```

### **Run the Optimization Notebook**

Open:

```
model.ipynb
```

and run all cells.
Make sure you have a valid **Gurobi license** (academic licenses are free).

---

## Outputs

The repository produces:

* A complete `networkx` subway multi-graph
* Cleaned station-level rush-hour demand
* Train frequencies per line (optimized)
* Comparison against published GTFS schedules
* Visualizations and summary metrics (from notebooks)

---

## Data Sources

* **NYC Subway Hourly Ridership (2020–2024)**
  NYC Open Data — `wujg-7c2s`
* **MTA GTFS Data (static)**
  [https://www.mta.info/developers](https://www.mta.info/developers)
* **MTA Subway Stations Dataset**
  NYC Open Data — `39hk-dx4f`

---
