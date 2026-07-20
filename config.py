"""Global configuration constants for the warehouse simulation."""

NUM_AISLES = 10
POSITIONS_PER_AISLE = 20
LOCATION_SPACING = 1.0  # meters between adjacent positions in same aisle
AISLE_SPACING = 2.5  # meters between adjacent aisles
TOTAL_SKUS = 400

PICKER_SPEED = 1.0  # m/s walking speed
PICK_TIME_PER_ITEM = 3.0  # seconds per item

ORDER_ARRIVAL_MEAN = 300.0  # mean inter-arrival time (seconds), ~5 min
ORDER_SKUS_MIN = 5
ORDER_SKUS_MAX = 15

NUM_PICKERS = 2
SIMULATION_DURATION = 28800  # 8 hours in seconds
WARMUP_PERIOD = 3600  # 1 hour warmup period

NUM_REPLICATIONS = 30
GA_POP_SIZE = 50
GA_GENERATIONS = 100
GA_TOURNAMENT_SIZE = 3
GA_CROSSOVER_PROB = 0.8
GA_MUTATION_PROB = 0.2
GA_ELITISM = 2
