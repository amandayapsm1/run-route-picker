# Run Route Picker

I run a lot, and picking a route in Singapore's weather is a real decision: a shaded trail is great at 32°C and a bad idea in a thunderstorm. This tool takes **how far I want to run, what the session is for, and today's weather**, and ranks routes with a score I can explain.

No dependencies, just Python 3.9+.

## Try it

```bash
python pick_route.py --distance 10 --goal easy --temp 32 --rain none
python pick_route.py --distance 6 --goal hills --temp 28 --rain heavy
python pick_route.py --distance 5 --goal tempo --temp 30 --haze high
```

Options: `--goal` easy | tempo | long | hills | trail, `--rain` none | light | heavy, `--haze` low | moderate | high, `--top N`.

## How it scores (100 points)

| Factor | Max | Logic |
|---|---|---|
| Distance | 40 | Full marks within 10% of target, falling to zero at 50% off |
| Goal fit | 30 | Climb per km vs what the session needs, plus surface (paved vs trail) |
| Weather | 30 | Heat penalises exposed routes, rain penalises unsheltered and slippery trails, haze penalises long exposure |

Every result shows its points breakdown and a short note on why (e.g. "good shade for the heat"), so you can see the reasoning rather than trusting a black box.

## Data

`routes.csv` holds 10 Singapore routes. Distances, elevation, shade and shelter figures are **rough estimates for illustration**, so replace them with your own routes (columns: `name, distance_km, elevation_m, shade_pct, sheltered_pct, surface, loop`).

## Ideas to extend it

- Pull live temperature, rain and PSI from a weather API instead of typing them in
- Import routes from a Strava or Garmin GPX export
- Learn the weights from which routes I actually enjoyed
- Add a time-of-day input (sunrise, evening shade)
