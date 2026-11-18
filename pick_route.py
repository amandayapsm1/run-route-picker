#!/usr/bin/env python3
"""Run Route Picker: choose a run based on distance, training goal and weather.

Scores every route in routes.csv (0-100) with transparent rules and explains
why each one ranks where it does. Standard library only.

Examples:
    python pick_route.py --distance 10 --goal easy --temp 31 --rain none
    python pick_route.py --distance 6 --goal hills --temp 28 --rain light
    python pick_route.py --distance 12 --goal long --temp 33 --rain none --haze high
"""
import argparse
import csv
import os
import sys

# Points available per factor (sum = 100). Edit to change what matters to you.
WEIGHTS = {"distance": 40, "goal": 30, "weather": 30}

GOALS = {
    # goal: (ideal elevation gain per km, prefers_trail)
    "easy": (5, False),     # flat, comfortable
    "tempo": (5, False),    # flat and fast, steady surface
    "long": (10, False),    # distance-friendly, some variety
    "hills": (25, True),    # climbing
    "trail": (15, True),    # off-road
}
RAIN_LEVELS = {"none": 0, "light": 1, "heavy": 2}
HAZE_LEVELS = {"low": 0, "moderate": 1, "high": 2}


def distance_score(route_km, target_km):
    """100% if within 10% of target; falls off linearly to 0 at 50% off."""
    gap = abs(route_km - target_km) / target_km
    if gap <= 0.10:
        return 1.0
    return max(0.0, 1 - (gap - 0.10) / 0.40)


def goal_score(route, goal):
    ideal_per_km, wants_trail = GOALS[goal]
    per_km = route["elevation_m"] / route["distance_km"]
    # Closeness of climb rate to the ideal (within 10 m/km of ideal => partial)
    climb_fit = max(0.0, 1 - abs(per_km - ideal_per_km) / 20)
    surface_fit = 1.0 if (wants_trail == (route["surface"] in ("trail", "mixed"))) else 0.5
    if goal in ("tempo", "easy") and route["surface"] == "paved":
        surface_fit = 1.0
    return 0.7 * climb_fit + 0.3 * surface_fit


def weather_score(route, temp_c, rain, haze):
    s = 1.0
    notes = []
    # Heat: shade matters above 30C
    if temp_c >= 30:
        shade_gap = (100 - route["shade_pct"]) / 100
        s -= 0.6 * shade_gap
        if route["shade_pct"] >= 70:
            notes.append("good shade for the heat")
        elif route["shade_pct"] < 30:
            notes.append("exposed in the heat")
    # Rain: shelter matters, slippery trails are penalised
    r = RAIN_LEVELS[rain]
    if r:
        s -= 0.25 * r * (1 - route["sheltered_pct"] / 100)
        if route["surface"] == "trail":
            s -= 0.2 * r
            notes.append("trail may be slippery")
        if route["sheltered_pct"] >= 30:
            notes.append("has sheltered sections")
    # Haze: prefer shorter/lower-intensity exposure
    h = HAZE_LEVELS[haze]
    if h:
        s -= 0.15 * h * min(route["distance_km"] / 10, 1.5)
        if h == 2:
            notes.append("consider a shorter run in heavy haze")
    return max(0.0, min(1.0, s)), notes


def score(route, args):
    d = distance_score(route["distance_km"], args.distance)
    g = goal_score(route, args.goal)
    w, notes = weather_score(route, args.temp, args.rain, args.haze)
    parts = {
        "distance": round(WEIGHTS["distance"] * d, 1),
        "goal": round(WEIGHTS["goal"] * g, 1),
        "weather": round(WEIGHTS["weather"] * w, 1),
    }
    return round(sum(parts.values()), 1), parts, notes


def load_routes(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("distance_km", "elevation_m", "shade_pct", "sheltered_pct"):
            r[k] = float(r[k])
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--distance", type=float, required=True, help="target distance in km")
    p.add_argument("--goal", choices=GOALS, default="easy")
    p.add_argument("--temp", type=float, default=29, help="temperature in C (default 29)")
    p.add_argument("--rain", choices=RAIN_LEVELS, default="none")
    p.add_argument("--haze", choices=HAZE_LEVELS, default="low")
    p.add_argument("--routes", default=os.path.join(here, "routes.csv"))
    p.add_argument("--top", type=int, default=3)
    args = p.parse_args()

    if args.distance <= 0:
        sys.exit("--distance must be greater than 0")

    ranked = []
    for r in load_routes(args.routes):
        total, parts, notes = score(r, args)
        ranked.append((total, parts, notes, r))
    ranked.sort(key=lambda x: x[0], reverse=True)

    print(f"Goal: {args.goal} | {args.distance:g} km | {args.temp:g}C | rain: {args.rain} | haze: {args.haze}\n")
    print(f"{'#':<3}{'Route':<42}{'km':>5}{'Score':>7}   Dist/Goal/Weather")
    print("-" * 78)
    for i, (total, parts, notes, r) in enumerate(ranked[: args.top], 1):
        print(f"{i:<3}{r['name']:<42}{r['distance_km']:>5g}{total:>7}   "
              f"{parts['distance']:g}/{parts['goal']:g}/{parts['weather']:g}")
        if notes:
            print(f"   note: {'; '.join(notes)}")


if __name__ == "__main__":
    main()
