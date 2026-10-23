"""
Centrality & Key Influencer Analysis Service (MHA NCRB Criminal Network Engine)

Implements pure-Python graph analytics for law enforcement:
1. Degree Centrality (Operational Enforcers / High Volume communicators)
2. Betweenness Centrality via Brandes' Algorithm (Brokers / Hawala Intermediaries bridging cells)
3. PageRank Centrality via Power Iteration (Kingpins / Masterminds commanding key lieutenants)
4. Connected Components & Module Partitioning (Criminal Gang Cells)
"""

from collections import defaultdict, deque
from typing import Any


def compute_pagerank(
    nodes: list[str],
    adj: dict[str, list[str]],
    damping: float = 0.85,
    max_iter: int = 50,
    tol: float = 1e-6
) -> dict[str, float]:
    """Computes PageRank centrality to identify criminal Kingpins/Masterminds."""
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: 1.0}

    # Reverse adjacency for incoming links
    incoming: dict[str, list[str]] = defaultdict(list)
    out_degree: dict[str, int] = defaultdict(int)
    for u in nodes:
        for v in adj.get(u, []):
            incoming[v].append(u)
            out_degree[u] += 1

    rank = {node: 1.0 / n for node in nodes}

    for _ in range(max_iter):
        next_rank = {}
        dangling_sum = sum(rank[u] for u in nodes if out_degree[u] == 0)
        dangling_contrib = damping * (dangling_sum / n)

        diff = 0.0
        for u in nodes:
            in_sum = sum(rank[v] / out_degree[v] for v in incoming[u] if out_degree[v] > 0)
            new_r = (1.0 - damping) / n + dangling_contrib + damping * in_sum
            diff += abs(new_r - rank[u])
            next_rank[u] = new_r

        rank = next_rank
        if diff < tol:
            break

    # Normalize max to 1.0
    max_val = max(rank.values()) if rank else 1.0
    return {k: round(v / max_val, 4) for k, v in rank.items()}


def compute_betweenness_centrality(
    nodes: list[str],
    adj: dict[str, list[str]]
) -> dict[str, float]:
    """
    Computes Betweenness Centrality using Brandes' Algorithm.
    Identifies Brokers / Intermediaries whose removal fractures the network.
    """
    cb = {node: 0.0 for node in nodes}
    n = len(nodes)
    if n <= 2:
        return cb

    for s in nodes:
        stack = []
        pred: dict[str, list[str]] = defaultdict(list)
        sigma = defaultdict(int)
        sigma[s] = 1
        dist = {node: -1 for node in nodes}
        dist[s] = 0
        q = deque([s])

        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj.get(v, []):
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)

        delta = defaultdict(float)
        while stack:
            w = stack.pop()
            for v in pred[w]:
                c = (sigma[v] / sigma[w]) * (1.0 + delta[w])
                delta[v] += c
            if w != s:
                cb[w] += delta[w]

    # Normalize by (n-1)*(n-2) for directed graph
    norm = (n - 1) * (n - 2) if n > 2 else 1.0
    max_val = max(cb.values()) if cb else 1.0
    if max_val == 0.0:
        max_val = 1.0

    return {k: round(v / max_val, 4) for k, v in cb.items()}


def detect_network_modules(
    nodes: list[str],
    adj: dict[str, list[str]]
) -> dict[str, str]:
    """Partitions network into interconnected sub-modules/gangs using BFS components."""
    visited = set()
    modules = {}
    module_counter = 1

    for node in nodes:
        if node not in visited:
            module_name = f"CELL-{module_counter:02d}"
            queue = deque([node])
            visited.add(node)
            while queue:
                curr = queue.popleft()
                modules[curr] = module_name
                # traverse undirected
                neighbors = set(adj.get(curr, []))
                for other, nbrs in adj.items():
                    if curr in nbrs:
                        neighbors.add(other)
                for nbr in neighbors:
                    if nbr not in visited and nbr in set(nodes):
                        visited.add(nbr)
                        queue.append(nbr)
            module_counter += 1

    return modules


def analyze_criminal_network_influencers(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Analyzes the full network and labels each suspect with:
    - role: KINGPIN | BROKER | COORDINATOR | OPERATIVE
    - influence_score: 0 to 100
    - sub_gang_module: CELL-01, CELL-02, etc.
    """
    node_ids = [e["entity_id"] for e in entities if isinstance(e.get("entity_id"), str)]
    node_set = set(node_ids)

    adj: dict[str, list[str]] = defaultdict(list)
    degree_counts: dict[str, int] = defaultdict(int)

    for rel in relationships:
        s = rel.get("subject_entity_id")
        o = rel.get("object_entity_id")
        if s in node_set and o in node_set and s != o:
            adj[s].append(o)
            degree_counts[s] += 1
            degree_counts[o] += 1

    # 1. Algorithmic scores
    pagerank_scores = compute_pagerank(node_ids, adj)
    betweenness_scores = compute_betweenness_centrality(node_ids, adj)
    modules = detect_network_modules(node_ids, adj)

    max_degree = max(degree_counts.values()) if degree_counts else 1

    enhanced_entities = []
    kingpins = []
    brokers = []

    for ent in entities:
        eid = ent.get("entity_id")
        if not eid or eid not in node_set:
            enhanced_entities.append(ent)
            continue

        deg = degree_counts.get(eid, 0)
        pr = pagerank_scores.get(eid, 0.0)
        bw = betweenness_scores.get(eid, 0.0)
        mod = modules.get(eid, "CELL-01")

        # Determine Role
        if pr >= 0.70 and deg <= (max_degree * 0.75):
            role = "KINGPIN"
            kingpins.append(ent.get("name") or eid)
        elif bw >= 0.60:
            role = "BROKER"
            brokers.append(ent.get("name") or eid)
        elif deg >= (max_degree * 0.60) and max_degree > 2:
            role = "COORDINATOR"
        else:
            role = "OPERATIVE"

        # Composite Influence Score (0 - 100)
        raw_influence = (pr * 0.45) + (bw * 0.35) + ((deg / max_degree) * 0.20)
        influence_score = int(round(raw_influence * 100))

        enhanced_entities.append({
            **ent,
            "role": role,
            "influence_score": max(5, min(100, influence_score)),
            "sub_gang_module": mod,
            "metrics": {
                "degree": deg,
                "pagerank": pr,
                "betweenness": bw,
            }
        })

    return {
        "entities": enhanced_entities,
        "syndicate_analysis": {
            "identified_kingpins": kingpins,
            "identified_brokers": brokers,
            "cell_count": len(set(modules.values())),
            "most_connected_degree": max_degree,
        }
    }
