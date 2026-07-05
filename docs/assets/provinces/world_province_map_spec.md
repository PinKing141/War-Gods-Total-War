# Custom world province map

This asset pack attaches a CK2-style province layer to the custom world heightmap.

## Generated target assets

```text
docs/assets/heightmaps/world_heightmap_3072x2048_16bit.png
docs/assets/provinces/world_provinces_unique_rgb_3072x2048.png
docs/assets/provinces/world_province_painted_3072x2048.png
docs/assets/provinces/world_province_preview_labeled_1536x1024.png
docs/assets/provinces/world_province_definitions.csv
docs/assets/provinces/world_province_adjacency.csv
docs/assets/provinces/world_map_manifest.json
```

## Map scale

```text
3072 x 2048
670 land provinces
9 named seed-frontier provinces preserved from the lore CSV
```

## Province-map rule

The machine province map must be the unique-RGB file, not the painted preview.

```text
water = RGB 0,0,0
each land province = one unique RGB value
province_definitions.csv maps RGB values to province IDs, names, region, terrain, controller and strategic values
```

## Lore placement logic

The province layout follows the rebuilt War Gods geography:

- Rov Basin around the old canal/road heartland
- Greyhook Spine as the mountain-pass and mine spine
- Cairn March as the cold northern frontier
- Taluun Steppe as the eastern horse zone
- Qeresh Wells across the southern drylands and salt routes
- Maren Coast around the Lanter Sea ports and river mouths
- Fenward as wet forest/marsh frontier
- Bannerfields as western grain and cavalry estates

The seed-frontier conflict zone is placed where the Rov Basin, Cairn March, Gharu freeholds, Kavari pass towns, Maren trade influence, Nalari charter law, Taluun horse pressure and the Nine Banners temple order collide.

## Do not use the preview as data

The labeled preview is only for human checking. It has blended colors, labels and border darkening. Use the unique-RGB PNG and CSV for engine parsing.
