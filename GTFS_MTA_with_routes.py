# -*- coding: utf-8 -*-
"""
Created on Tue May  8 17:48:55 2018

@author: roland

inspired by https://github.com/paulgb/gtfs-gexf/blob/master/transform.py
"""

import networkx as nx
# import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from csv import DictReader
from itertools import groupby
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")   # or "SVG", "PDF", etc.
import matplotlib.pyplot as plt

import csv
import numpy as np


DATA_ROOT = "C:\\Users\\Administrator\\GTFS-NetworkX\\datasets\\"
TRIPS_FILE = f'{DATA_ROOT}trips.txt'
ROUTES_FILE = f'{DATA_ROOT}routes.txt'
STOPS_FILE = f'{DATA_ROOT}stops.txt'

INCLUDE_AGENCIES = ['MTA NYCT']

IGNORE_ROUTE = [
    'RTTA_DEF',  # out of service
    'RTTA_REV',  # revenue train (charter)
    'BL_1b', 'BL_1c', 'BL_1d', 'BL_1e'
]

# MultiGraph so we can have multiple edges (routes) between same stations
G = nx.MultiGraph()


def get_stop_id(stop_id):
    """Translate stop_id to parent_stop_id if available."""
    if STOPS[stop_id]['parent_station'] == '':
        return stop_id
    else:
        return STOPS[stop_id]['parent_station']


def add_stop_to_graph(G, stop_id):
    """Add stop as new node to graph (using parent stop if available)."""
    node = STOPS[get_stop_id(stop_id)]

    if node['stop_id'] not in G.nodes:
        G.add_node(
            node['stop_id'],
            stop_name=node['stop_name'],
            stop_lon=node['stop_lon'],
            stop_lat=node['stop_lat'],
        )
    return G


def add_edge_to_graph(G, from_id, to_id, route_short_name):
    """
    Add edge to graph between from_id and to_id for a given route_short_name.
    Uses route_short_name as the edge key in the MultiGraph.

    If an edge with this key already exists, increment the 'count' attribute.
    """
    u = get_stop_id(from_id)
    v = get_stop_id(to_id)

    edge_data = G.get_edge_data(u, v, route_short_name, default=None)
    if edge_data is None:
        # first time we see this (u, v, route) combo
        G.add_edge(u, v, key=route_short_name, count=1)
    else:
        # already saw this route between these two stops; increment count
        G.add_edge(u, v, key=route_short_name, count=edge_data['count'] + 1)


def load_routes(filename):
    """Include only routes from agencies we are interested in."""
    routes_csv = DictReader(open(filename, 'r'))
    routes_dict = dict()
    for route in routes_csv:
        if (route['agency_id'] in INCLUDE_AGENCIES and
                route['route_id'] not in IGNORE_ROUTE):

            routes_dict[route['route_id']] = route
    print('routes', len(routes_dict))
    return routes_dict


def load_trips(filename, routes_dict):
    """
    Load trips from file, only include trips on routes we are interested in.
    """
    trips_csv = DictReader(open(filename, 'r'))
    trips_dict = dict()
    for trip in trips_csv:
        if trip['route_id'] in routes_dict:
            trip['color'] = routes_dict[trip['route_id']]['route_color']
            trip['route_short_name'] = routes_dict[trip['route_id']]['route_short_name']
            trips_dict[trip['trip_id']] = trip
    print('trips', len(trips_dict))
    return trips_dict


def load_stops(filename):
    stops_csv = DictReader(open(filename, 'r'))
    stops_dict = dict()
    for stop in stops_csv:
        stops_dict[stop['stop_id']] = stop
    print('stops', len(stops_dict))
    return stops_dict


# ==============================================

ROUTES = load_routes(filename=ROUTES_FILE)
TRIPS = load_trips(filename=TRIPS_FILE, routes_dict=ROUTES)
STOPS = load_stops(filename=STOPS_FILE)

stop_times_csv = DictReader(open(f'{DATA_ROOT}stop_times.txt', 'r'))

stops = set()
# IMPORTANT: store ALL (from, to, route) combinations, not just one per pair
edges = []

for trip_id, stop_time_iter in groupby(stop_times_csv, lambda st: st['trip_id']):
    if trip_id in TRIPS:
        trip = TRIPS[trip_id]
        route_short_name = trip['route_short_name']

        # groupby yields an iterator; materialize it so we can safely walk it
        stop_times = list(stop_time_iter)
        if len(stop_times) < 2:
            continue

        prev_stop = stop_times[0]['stop_id']
        stops.add(prev_stop)

        for stop_time in stop_times[1:]:
            stop = stop_time['stop_id']
            stops.add(stop)
            edges.append((prev_stop, stop, route_short_name))
            prev_stop = stop

print('stops', len(stops))
print('edges (trip segments)', len(edges))

# Add nodes
for stop_id in STOPS:
    if stop_id in stops:
        add_stop_to_graph(G, stop_id)
print('Nodes:', G.number_of_nodes())

# Add edges to MultiGraph, preserving route dimension
for start_stop_id, end_stop_id, route_short_name in edges:
    add_edge_to_graph(
        G,
        from_id=start_stop_id,
        to_id=end_stop_id,
        route_short_name=route_short_name
    )
print('Edges (MultiGraph):', G.number_of_edges())


# ================================
# Build indices + CSV exports
# ================================

# Node indices
nodes = list(G.nodes())
node_index = {node: i for i, node in enumerate(nodes)}

# Route indices (one index per route_short_name actually in the graph)
routes_in_graph = sorted({key for _, _, key in G.edges(keys=True)})
route_index = {r: k for k, r in enumerate(routes_in_graph)}

print("Num nodes:", len(nodes))
print("Num routes:", len(routes_in_graph))

# --- NODES TABLE ---
with open('nodes_v2.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['node_idx', 'stop_id', 'stop_name', 'stop_lon', 'stop_lat'])
    for stop_id in nodes:
        attrs = G.nodes[stop_id]
        writer.writerow([
            node_index[stop_id],
            stop_id,
            attrs.get('stop_name', ''),
            attrs.get('stop_lon', ''),
            attrs.get('stop_lat', '')
        ])

# --- ROUTES TABLE ---
with open('routes_v2.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['route_idx', 'route_short_name'])
    for r, k in route_index.items():
        writer.writerow([k, r])

# --- EDGES TABLE WITH ROUTE DIMENSION (for x_i_j_r) ---
with open('edges_by_route_v2.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'edge_idx',
        'from_idx', 'to_idx',
        'route_idx',
        'from_stop_id', 'to_stop_id',
        'route_short_name',
        'count'
    ])

    for edge_idx, (u, v, r, data) in enumerate(G.edges(keys=True, data=True)):
        i = node_index[u]
        j = node_index[v]
        k = route_index[r]
        cnt = data.get('count', 1)
        writer.writerow([
            edge_idx,
            i, j,
            k,
            u, v,
            r,
            cnt
        ])

print("Wrote nodes.csv, routes.csv, edges_by_route.csv")


# ================================
# Plotting (same as before)
# ================================

deg = nx.degree(G)
labels = {
    stop_id: G.nodes[stop_id].get('stop_name', '') if deg[stop_id] >= 0 else ''
    for stop_id in G.nodes
}

# Build pos dict with numeric lon/lat
pos = {}
for stop_id in G.nodes:
    try:
        lon = float(G.nodes[stop_id]['stop_lon'])
        lat = float(G.nodes[stop_id]['stop_lat'])
        pos[stop_id] = (lon, lat)
    except (KeyError, TypeError, ValueError):
        # Skip nodes without valid numeric coordinates
        continue

# lon/lat data is in PlateCarree projection
data_crs = ccrs.PlateCarree()

fig = plt.figure(figsize=(20, 20))
ax = plt.axes(projection=ccrs.PlateCarree())

nx.draw_networkx(
    G,
    ax=ax,
    # labels=labels,  # optional: labels clutter the map
    pos=pos,
    node_size=2,
    # transform=data_crs,  # NetworkX doesn't take this; see earlier notes if needed
)

# ax.set_axis_off()

plt.show(block=True)
fig.savefig('gtfs_networkx_map_with_routes.png', dpi=300)
