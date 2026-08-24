# simulation/ — ABM Module Guide

This directory contains the Agent-Based Model (ABM) that implements Stage 2 of
the SEEM methodology: simulating large-scale emergency evacuation in
Île-de-France with Social Vulnerability Index (SVI)-driven agent behavior.

For the full project overview, see the [root README](../README.md).

---

## Quick Start

```bash
# From the project root
python scripts/main.py
```

Expected runtime: 10–60 minutes per run depending on hardware and agent count.
Progress is logged per simulation time step.

Results are written to:

- `outputs/simulation_runs/evacuation_simulation_{run_id}/` — per-run JSON metadata
- `outputs/agent_states/final_agent_states.csv` — agent states at simulation end
- `outputs/agent_states/fallback_agent_states.csv` — agents requiring fallback routing
- `outputs/figures/` — all generated plots

---

## Module Interaction Map

The simulation has a clear dependency chain from data loading through to metrics
export:

```
scripts/main.py                          ← entry point
    │
    ├─ reads: simulation/configs/evacuation_simulation.json
    │         (scenario parameters, SVI behavioral mappings, output paths)
    │
    ├─ calls: simulation/preparing_resources.py
    │         └─ loads OSM GraphML networks into memory
    │            (data/maps/osmnx_layers/*.graphml)
    │         └─ validates IDFM GTFS timetables
    │            (data/maps/IDFM-gtfs/*.csv)
    │
    ├─ calls: simulation/space/pre_process_amenities.py
    │         └─ builds an index of shelters, schools, hospitals
    │            from OSM amenity data
    │            (data/maps/osmnx_layers/idf_amenities.csv)
    │
    ├─ calls: simulation/space/evacuation_area_initializer.py
    │         └─ defines the 50 km evacuation zone centred on Paris
    │         └─ assigns each agent a target safe destination
    │         └─ uses pre-computed geometry cache
    │            (simulation/space/cache/*.json)
    │
    └─ calls: simulation/model/agents_model_initializer.py
              └─ reads SVI scores and mode assignments from config
              └─ instantiates one EvacuationAgent per individual
                 (simulation/model/evacuation_model.py)
                 │
                 Each agent per time step:
                 ├─ checks activation delay (SVI-driven)
                 ├─ selects mode (walk / bike / MPV / PT)
                 ├─ routes via Dijkstra on the mode-appropriate GraphML
                 ├─ updates position, distance, congestion state
                 └─ transitions to ARRIVED / EVACUATING / FAILED
              │
              └─ calls at run end: simulation/model/simulation_analytics.py
                                   └─ computes equity metrics per SVI quartile
                                   └─ writes CSVs to outputs/agent_states/
                                   └─ writes figures to outputs/figures/
```

### Execution flow summary

| Step | Module                           | Action                                    |
|------|----------------------------------|-------------------------------------------|
| 1    | `preparing_resources.py`         | Load and validate all network data        |
| 2    | `pre_process_amenities.py`       | Build shelter/destination index           |
| 3    | `evacuation_area_initializer.py` | Define zone, assign destinations          |
| 4    | `agents_model_initializer.py`    | Filter & instantiate active evacuation agents (590 agents in zone out of 3,337 survey individuals) |
| 5    | `evacuation_model.py` (×N steps) | Simulate each agent per time step         |
| 6    | `simulation_analytics.py`        | Export results and generate figures       |

---

## Configuration & Output Flow

The simulation configuration and run metadata are automatically generated and saved to `simulation/configs/evacuation_simulation.json` at the conclusion of each simulation run by `scripts/main.py` (via AgentPy's `results.save()` / `save_results_manually()`).

> [!NOTE]
> **Agent Population Filtering**: While `data/individuals_dataset.csv` contains 3,337 total survey individuals (~3,300+ full NetMob25 survey scale), `AgentsGatherer` filters for individuals who have valid, active GPS traces located **inside the active 50 km evacuation zone polygon** around Paris on the scenario date. This produces 590 active agents (`created_objects: 590`) in the simulation run.

### Key configuration and metadata structure (`evacuation_simulation.json`)

```json
{
  "info": {
    "model_type": "EvacuationModel",
    "time_stamp": "2025-09-07 03:32:34",
    "agentpy_version": "0.1.5",
    "python_version": "3.12",
    "experiment": false,
    "completed": true,
    "created_objects": 590,
    "completed_steps": 180,
    "run_time": "1:06:36.960250"
  },
  "parameters": {
    "constants": {
      "start_datetime": "2023-01-01T08:00:00",
      "step_seconds": 60,
      "svi_speed_penalty": 0.5,
      "max_svi_start_delay_s": 1800,
      "base_patience_s": 300,
      "graphml_path_drive": "data/maps/osmnx_layers/IDF_drive_network.graphml",
      "graphml_path_walk": "data/maps/osmnx_layers/IDF_walk_network.graphml",
      "graphml_path_cycle": "data/maps/osmnx_layers/IDF_bike_network.graphml",
      "amenities_df": "data/maps/osmnx_layers/idf_amenities.csv"
    }
  }
}
```

The behavioral parameters are the core of the SVI-to-simulation linkage:

| Parameter    | Description                                                                      | SVI effect                 |
|--------------|----------------------------------------------------------------------------------|----------------------------|
| `delay_sec`  | Seconds before an agent begins evacuating after the crisis event                 | Higher SVI → longer delay  |
| `speed_mult` | Fraction of the nominal network speed the agent achieves                         | Higher SVI → slower        |
| `patience`   | Fraction of nominal patience before the agent fails to reroute around congestion | Higher SVI → less tolerant |

---

## Input / Output Mapping

### Inputs

| Input           | Path                                                        | Format   | Description                                                   |
|-----------------|-------------------------------------------------------------|----------|---------------------------------------------------------------|
| Walk network    | `data/maps/osmnx_layers/IDF_walk_network.graphml`           | GraphML  | Pedestrian road graph for IDF                                 |
| Bike network    | `data/maps/osmnx_layers/IDF_bike_network.graphml`           | GraphML  | Cycling road graph                                            |
| Drive network   | `data/maps/osmnx_layers/IDF_drive_network.graphml`          | GraphML  | Motorized vehicle road graph                                  |
| Transit network | `data/maps/osmnx_layers/IDF_transportation_network.graphml` | GraphML  | Multimodal combined graph                                     |
| GTFS timetables | `data/maps/IDFM-gtfs/*.csv`                                 | GTFS CSV | IDF public transit schedules (IDFM)                           |
| Amenities       | `data/maps/osmnx_layers/idf_amenities.csv`                  | CSV      | OSM amenity locations (shelters, schools, hospitals)          |
| OSM raw         | `data/maps/osm_chunks_pyrosm/*.osm.pbf`                     | PBF      | Raw OSM extract for IDF (5 chunks)                            |
| Config          | `simulation/configs/evacuation_simulation.json`             | JSON     | Scenario + behavioral parameters                              |
| Summary config  | `simulation/configs/simulation_summary.json`                | JSON     | Aggregate run summary                                         |
| Route cache     | `simulation/space/cache/*.json`                             | JSON     | Pre-computed geometries (21 files, speeds up spatial lookups) |

### Intermediate artifacts

| Artifact             | Location                  | Description                                             |
|----------------------|---------------------------|---------------------------------------------------------|
| Route geometry cache | `simulation/space/cache/` | Cached shortest-path geometries; populated on first run |
| Network objects      | In-memory (not persisted) | OSM GraphML loaded into NetworkX graph objects          |
| Agent population     | In-memory (not persisted) | Mesa Agent objects, one per individual                  |

### Outputs

| Output             | Path                                                                          | Format | Description                                          |
|--------------------|-------------------------------------------------------------------------------|--------|------------------------------------------------------|
| Per-run info       | `outputs/simulation_runs/evacuation_simulation_{i}/info.json`                 | JSON   | Run metadata (timestamp, seed, agent count)          |
| Per-run params     | `outputs/simulation_runs/evacuation_simulation_{i}/parameters_constants.json` | JSON   | Exact parameters for that run                        |
| Final agent states | `outputs/agent_states/final_agent_states.csv`                                 | CSV    | Agent state at end of simulation                     |
| Fallback states    | `outputs/agent_states/fallback_agent_states.csv`                              | CSV    | Agents that triggered fallback routing logic         |
| Trial statistics   | `outputs/agent_states/simulation_outcomes/Agents_Statistics_Trial.csv`        | CSV    | Aggregate per-trial statistics                       |
| Enhanced summary   | `outputs/agent_states/simulation_outcomes/Enhanced_Agent_Summary.csv`         | CSV    | Full per-agent summary with derived metrics          |
| Journey segments   | `outputs/agent_states/simulation_outcomes/Journey_Segments_Detail.csv`        | CSV    | Per-segment journey breakdown (mode, distance, time) |
| Figures            | `outputs/figures/**/*.png`                                                    | PNG    | All analysis plots (organized by sub-category)       |
| Interactive maps   | `outputs/figures/evacuation_maps/*.html`                                      | HTML   | Folium maps with agent traces and SVI coloring       |

### Agent state schema (`final_agent_states.csv`)

| Column                    | Type        | Description                                     |
|---------------------------|-------------|-------------------------------------------------|
| `agent_id`                | str         | Unique agent identifier                         |
| `svi_score`               | float [0,1] | Continuous SVI (higher = more vulnerable)       |
| `svi_quartile`            | str         | Low / Moderate / High / Very_High               |
| `primary_mode`            | str         | Walking / Bike / MPV / PT                       |
| `final_status`            | str         | ARRIVED / EVACUATING / FAILED                   |
| `evacuation_time_min`     | float / NaN | Minutes to reach safe zone (NaN if not arrived) |
| `distance_travelled_km`   | float       | Total network distance covered                  |
| `destination_distance_km` | float       | Great-circle distance to assigned destination   |
| `age`                     | int         | Agent age                                       |
| `sex`                     | int         | Encoded sex (0 = Man, 1 = Woman)                |
| `nb_car`                  | float       | Number of cars in household (transformed)       |
| `pmr`                     | int         | Reduced mobility indicator                      |

Agent terminal states are defined as:

- **ARRIVED**: agent reached a designated safe destination within the simulation horizon
- **EVACUATING**: agent was actively traversing the network at simulation end (right-censored)
- **FAILED**: agent could not find a feasible path or reroute to safety

---

## Results Location

| Result type                    | Directory                                             |
|--------------------------------|-------------------------------------------------------|
| SVI distribution, CDF, Q-Q     | `outputs/figures/svi_analysis/`                       |
| Feature × SVI correlations     | `outputs/figures/relationships_with_svi/`             |
| Nonlinear transform plots      | `outputs/figures/relationships_with_transformations/` |
| PCA / t-SNE validation         | `outputs/figures/dimensionality_reduction/`           |
| SVI → behavioral param plots   | `outputs/figures/behavioral_modeling/`                |
| Evacuation equity analytics    | `outputs/figures/evacuation_analytics/`               |
| Agent trace maps (interactive) | `outputs/figures/evacuation_maps/`                    |
| Aggregate run logs             | `outputs/simulation_runs/`                            |
| Agent-level CSV data           | `outputs/agent_states/`                               |

---

## Extending Experiments

### Modifying scenario parameters

Scenario parameters (such as simulation steps, center latitude/longitude, evacuation radius, and network paths) are defined in `scripts/main.py` and passed into `run_simulation(parameters)`. To run a custom scenario:

1. Update or parameterize the `parameters` dictionary in `scripts/main.py` (e.g. adjust `MAX_SIMULATION_STEPS` or `SCENARIO_RADIUS_KM`).
2. Run `python scripts/main.py`.
3. The run metadata and execution output will automatically save to `simulation/configs/evacuation_simulation.json` and `simulation/configs/simulation_summary.json`.

### Modifying SVI behavioral parameters

Edit the behavioral parameter constants in `scripts/main.py` or `simulation/model/evacuation_model.py`. The parameters (`svi_speed_penalty`, `max_svi_start_delay_s`, `base_patience_s`) control SVI-driven behavior:

| Parameter               | Description                                                                      | SVI effect                 |
|-------------------------|----------------------------------------------------------------------------------|----------------------------|
| `max_svi_start_delay_s` | Seconds before an agent begins evacuating after the crisis event                 | Higher SVI → longer delay  |
| `svi_speed_penalty`     | Speed penalty factor applied to maximum agent velocity                           | Higher SVI → slower        |
| `base_patience_s`       | Base patience before an agent triggers fallback/rerouting due to network congestion | Higher SVI → less tolerant |

### Modifying agent step logic

The per-timestep agent behavior is in `simulation/model/evacuation_model.py`, in the `step()` method. The logic sequence is:

```
step():
  1. Check if activation_delay has elapsed → if not, remain idle
  2. If at destination → mark ARRIVED, stop
  3. Compute next move on mode-appropriate graph
  4. Check patience → if congestion exceeds threshold, mark FAILED or reroute
  5. Advance position, update distance, update time
```

### Adding a new transportation mode

1. Prepare the mode's OSM network and save it to `data/maps/osmnx_layers/` as a `.graphml` file.
2. Register the mode extraction in `IleDeFranceMobilityDataCollector.ile_de_france_open_street_map_()` in `simulation/preparing_resources.py` (adding it to the `networks` list).
3. Pass the graphml file path to `parameters` in `scripts/main.py`.
4. Handle the new mode in the agent `step()` logic in `simulation/model/evacuation_model.py`.

### Adding new equity metrics

Extend `simulation/model/simulation_analytics.py`. The analytics module receives
the full agent population as a list of `EvacuationAgent` objects at run end and
can compute any derived metric from their attributes. Add a new function and call
it from the `run_analytics()` entry point.

---

## Module Reference

| Module                                 | Key responsibility                                            |
|----------------------------------------|---------------------------------------------------------------|
| `preparing_resources.py`               | Load OSM GraphML and GTFS; validate data completeness         |
| `space/evacuation_area_initializer.py` | Define evacuation zone polygon; assign agent destinations     |
| `space/pre_process_amenities.py`       | Build geospatial index of shelters and safe destinations      |
| `model/agents_model_initializer.py`    | Read config + SVI scores; instantiate Mesa Agent objects      |
| `model/evacuation_model.py`            | Agent class: `__init__`, `step()`, routing, state transitions |
| `model/simulation_analytics.py`        | Post-simulation metrics, figure generation, CSV export        |
| `model/setup.py`                       | Package setup and optional compilation hooks                  |
