import json
import heapq


def load_input(filename):
    """
    Load the Level 1 graph from the input JSON file.
    """
    with open(filename, "r") as file:
        return json.load(file)


def dijkstra(graph, start, end):
    """
    Find the shortest path from start to end using Dijkstra's algorithm.

    Level 1 uses the 'weight' field as the edge cost.

    Returns:
        path: List of nodes representing the shortest route.
        distance: Total cost of the route.
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

    # Priority queue:
    # (current_distance, current_node)
    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(
            priority_queue
        )

        # Ignore an outdated queue entry.
        if current_distance > distances[current_node]:
            continue

        # Once the destination is removed from the queue,
        # its shortest distance has been found.
        if current_node == end:
            break

        # Examine every neighbour.
        for neighbour_info in graph[current_node]:

            neighbour = neighbour_info["node"]
            weight = neighbour_info["weight"]

            new_distance = current_distance + weight

            # Found a cheaper route to the neighbour.
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


def create_submission(path, filename):
    """
    Create the required JSON submission file.
    """

    output = {
        "route": path
    }

    with open(filename, "w") as file:
        json.dump(output, file, indent=4)


def main():
    # ---------------------------------------------------------
    # 1. Load input
    # ---------------------------------------------------------

    data = load_input("1.txt")

    graph = data["adjacency_list"]
    start = data["start"]
    end = data["end"]

    # ---------------------------------------------------------
    # 2. Find shortest route
    # ---------------------------------------------------------

    path, cost = dijkstra(
        graph,
        start,
        end
    )

    # ---------------------------------------------------------
    # 3. Validate route
    # ---------------------------------------------------------

    if not path:
        raise ValueError("No route was found.")

    if path[0] != start:
        raise ValueError("Route does not start at the required node.")

    if path[-1] != end:
        raise ValueError("Route does not end at the required node.")

    # ---------------------------------------------------------
    # 4. Create submission
    # ---------------------------------------------------------

    output_file = "level1_submission.txt"

    create_submission(
        path,
        output_file
    )

    # ---------------------------------------------------------
    # 5. Display result
    # ---------------------------------------------------------

    print("Level 1 solution completed.")
    print()
    print("Start:", start)
    print("End:", end)
    print("Shortest route:", " -> ".join(path))
    print("Route cost:", cost)
    print()
    print("Submission file:", output_file)


if __name__ == "__main__":
    main()