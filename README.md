A Python script that parses Adobe Animate XML files to extract, offset, and save specific SubTextures from sprite sheets as standalone transparent PNG files.

Commands:

List all available sprites
```bash
python sprite_extractor.py -l
```

Extract all sprites to extracted/ folder
```bash
python sprite_extractor.py -a
```

Extract specific sprite
```bash
python sprite_extractor.py -t "player_walk" -o extracted/player_walk.png
```

Command Options:

- `-l` : List all sprites
- `-a` : Extract all sprites
- `-t "name"` : Extract specific sprite
- `-o "path"` : Output file path
- `--offset X Y` : Apply X,Y offset