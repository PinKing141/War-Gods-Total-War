# CK3-style river visual target

The current river blend still does not match the CK2/CK3-style reference. The reference does not look like thin blue mask lines. It looks like a carved water feature integrated into province terrain.

## What the reference is doing

The Nile-style reference has several important visual rules:

```text
1. The main river is a dark, readable water body, not a thin blue line.
2. The river has strong dark outer banks.
3. The river is bordered by greener/fertile land.
4. The river width is stable and meaningful.
5. Tributaries and delta branches are thinner than the main river.
6. The river sits under labels, borders, armies and settlement icons.
7. Province borders cross over the river instead of the river destroying province readability.
8. The river mouth/delta is treated as a special wider feature.
```

## Why the previous output failed

The previous outputs treated `river_mask.png` like the visible final river art. That creates blue worm lines.

The correct approach is:

```text
river path = structure
river style renderer = final look
```

The mask should drive the renderer, but the renderer must build a full visual river body with banks, water depth, floodplain, and terrain tint.

## Required render layers

Use this order:

```text
1. province terrain base
2. floodplain/fertile tint around river
3. river bank darkening
4. outer carved channel shadow
5. main dark water body
6. inner muted blue-green water
7. subtle highlight only on the centerline
8. province borders
9. labels/icons/armies
```

## Style values

Do not use bright blue. Use muted, dark, map-style colours.

```text
outer bank/shadow: very dark blue-black or green-black
main water: deep blue-green / grey-blue
inner water: muted teal-blue
highlight: very subtle pale blue, low opacity
floodplain: green tint blended into nearby province terrain
sediment edge: muted brown/green, low opacity
```

## Width logic

The CK-style river should not use the literal exported path width as the final visible width. Width should be converted to cartographic river classes.

```text
width_class 1 = tiny stream, hidden unless zoomed in
width_class 2 = small tributary
width_class 3 = medium tributary
width_class 4 = major river
width_class 5 = huge river / navigable water body
```

Suggested visible widths at full map resolution:

```text
class 1: 2-3 px core, 5-8 px bank influence
class 2: 4-6 px core, 10-16 px bank influence
class 3: 8-12 px core, 18-28 px bank influence
class 4: 16-24 px core, 34-52 px bank influence
class 5: 26-44 px core, 60-90 px bank influence
```

These should scale with zoom.

## Delta rule

A delta is the one place where splitting is expected. Delta branches should:

```text
start near the river mouth
split into smaller distributaries
have wider floodplain/wetland tint
be visually connected to the coast/sea
not appear inland unless the terrain is marshland
```

## Renderer implementation target

The renderer should not draw `river_mask.png` directly. It should sample/use river masks and draw styled strokes from `river_paths.json`.

Required renderer behaviour:

```text
for each river path:
  draw floodplain influence under river
  draw thick dark bank/shadow stroke
  draw main water stroke
  draw inner water stroke
  draw subtle center highlight
  draw delta/wetland accent if type is delta or marsh_channel
```

Province borders and labels must be drawn after rivers.

## Workbench export target

The River Workbench should export both:

```text
river_paths.json = editable source paths and metadata
river masks = helper masks for terrain blending
```

The final CK-style visual should come from the renderer, not from a raw blue overlay.

## Acceptance test

The river pass is acceptable only if:

```text
main rivers look like map water bodies, not blue lines
major rivers are visibly wider than tributaries
floodplains subtly green the surrounding provinces
banks make rivers look carved into terrain
province borders and labels remain readable
river mouths and deltas blend into the sea
raw blue mask view is only a debug view, not the final view
```
