import json
import heapq
import itertools


def load_input(filename):
    """Load the Level 2 graph from the JSON input file."""
    with open(filename, "r") as file:
        return json.load(file)


def edge_cost(edge):
    """
    Calculate the effective Level 2 edge cost.

    Effective cost = time + risk
    """
    return edge["time"] + edge["risk"]


def dijkstra(graph, start, end):
    """
    Find the shortest path between start and end using Dijkstra's algorithm.

    Level 2 uses time + risk as the edge cost.

    Returns:
        path: shortest path as a list of nodes
        cost: total effective cost
    """

    distances = {
        node: float("inf")
        for node in graph
    }

    previous = {
        node: None
        for node in graph
    }

    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(
            priority_queue
        )

        # Ignore outdated entries.
        if current_distance > distances[current_node]:
            continue

        # We have reached the destination.
        if current_node == end:
            break

        for neighbour_info in graph[current_node]:

            neighbour = neighbour_info["node"]

            cost = edge_cost(neighbour_info)

            new_distance = current_distance + cost

            if new_distance < distances[neighbour]:

                distances[neighbour] = new_distance
                previous[neighbour] = current_node

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbour)
                )

    # Reconstruct the path.
    path = []

    current = end

    while current is not None:

        path.append(current)

        if current == start:
            break

        current = previous[current]

    path.reverse()

    return path, distances[end]


def evaluate_order(graph, start, end, station_order):
    """
    Evaluate one possible ordering of the required stations.

    The complete journey is:

    start -> station 1 -> station 2 -> ... -> station 4 -> end

    Returns:
        complete_path
        total_cost
    """

    checkpoints = (
        [start]
        + list(station_order)
        + [end]
    )

    total_cost = 0
    complete_path = []

    for i in range(len(checkpoints) - 1):

        leg_start = checkpoints[i]
        leg_end = checkpoints[i + 1]

        path, cost = dijkstra(
            graph,
            leg_start,
            leg_end
        )

        total_cost += cost

        # Add the entire first leg.
        if i == 0:
            complete_path.extend(path)

        # Skip the first node of later legs because
        # it is already the final node of the previous leg.
        else:
            complete_path.extend(path[1:])

    return complete_path, total_cost


def find_optimal_route(graph, start, end, required_stations):
    """
    Test every possible ordering of the required stations
    and return the cheapest complete route.
    """

    station_orders = itertools.permutations(
        required_stations
    )

    best_order = None
    best_path = None
    best_cost = float("inf")

    for order in station_orders:

        path, cost = evaluate_order(
            graph,
            start,
            end,
            order
        )

        if cost < best_cost:

            best_cost = cost
            best_order = order
            best_path = path

    return best_order, best_path, best_cost


def create_submission(path, filename):
    """Create the required JSON submission file."""

    output = {
        "route": path
    }

    with open(filename, "w") as file:
        json.dump(output, file, indent=4)


def main():

    # ---------------------------------------------------------
    # 1. Load input
    # ---------------------------------------------------------

    data = load_input("2.txt")

    graph = data["adjacency_list"]
    start = data["start"]
    end = data["end"]
    required_stations = data["required_stops"]

    # ---------------------------------------------------------
    # 2. Find optimal route
    # ---------------------------------------------------------

    best_order, best_path, best_cost = find_optimal_route(
        graph,
        start,
        end,
        required_stations
    )

    # ---------------------------------------------------------
    # 3. Validate route
    # ---------------------------------------------------------

    if not best_path:
        raise ValueError("No route was found.")

    if best_path[0] != start:
        raise ValueError(
            "Route does not start at the required node."
        )

    if best_path[-1] != end:
        raise ValueError(
            "Route does not end at the required node."
        )

    for station in required_stations:
        if station not in best_path:
            raise ValueError(
                f"Required station {station} was not visited."
            )

    # ---------------------------------------------------------
    # 4. Create submission
    # ---------------------------------------------------------

    output_file = "level2_submission.txt"

    create_submission(
        best_path,
        output_file
    )

    # ---------------------------------------------------------
    # 5. Display result
    # ---------------------------------------------------------

    print("Level 2 solution completed.")
    print()

    print("Start:", start)
    print("End:", end)

    print()

    print("Optimal station order:")
    print(" -> ".join(best_order))

    print()

    print("Complete route:")
    print(" -> ".join(best_path))

    print()

    print("Total effective cost:", best_cost)

    print()

    print("Submission file:", output_file)


if __name__ == "__main__":
    main()