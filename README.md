A Python script that parses Adobe Animate XML files to extract, offset, and save specific SubTextures from sprite sheets as standalone transparent PNG files.

Put your desired .xml and .png in "Imported" and use the commands below.

Commands:

List all available sprites
```bash
py sprite_extractor.py -l
```

Extract all sprites to extracted/ folder
```bash
py sprite_extractor.py -a
```

Extract all sprites (auto-yes to prompts)
```bash
py sprite_extractor.py -a -y
```

Extract specific sprite
```bash
py sprite_extractor.py -t "player_walk" -o extracted/player_walk.png
```

Command Options:

- `-l` : List all sprites
- `-a` : Extract all sprites
- `-t "name"` : Extract specific sprite
- `-o "path"` : Output file path
- `--offset X Y` : Apply X,Y offset
- `-y, --yes` : Automatically answer yes to all prompts