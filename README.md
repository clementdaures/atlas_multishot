# ATLAS MULTISHOT - ANDHAKARA
Pipeline repository for the animated short film Andhakara

## Version
1.00 — 12/10/26

## Designed For
SideFX Houdini 20.5 (Solaris / USD, Python 3.11, PySide2 / PySide6)

## Author
Clement Daures

- support@clementdaures.com (Pipeline TD / Dev / Rigging)

## Team
Léo Barachant (Animation 3D, Editing, Modeling)

Théo Berail (Storyboard, Scenario, Animation 3D)

Nino David (Modeling, Sculpting, Surfacing, Lighting)

Alicia Denux (Concept Art, Animation 3D)

Léa Genieys (Color Script, Lighting, Surfacing, Compositing)

Lilou Huet (Lighting, Modeling, Surfacing, Compositing)

Louna Perer (Grooming, CFX, Modeling, Surfacing)

Pablo Rodriguez (Scenario, Storyboard, FX, Layout)

Estelle Rupprecht (Concept Art, Cloth, CFX, Modeling)

Madelie Vaginay (Concept Art, Modeling, Surfacing, DMP)

## Logline
When her older sister accidentally dies in front of her, a stubborn teenager enters the world of the dead to bring back her soul.

## Repository Purpose
Atlas Multishot is a specialized Houdini Solaris tool built to organize lighting work across many shots and to speed up the export of lighting USD layers. Integrated directly into the technical pipeline of Andhakara alongside Atlas Manager, it provides:

- Shot assignment tools to distribute the shots of a sequence between lighting artists
- A shot selection panel that switches the `/stage` network to the active shot of the logged-in artist
- A multi-shot USD writer that exports several shots and render layers from a single `.hipnc` scene
- An intuitive PySide2 / PySide6 interface containing the assignment, selection and writer dialogs

## Tech Highlights
- **Shot Assignment & Selection:** Shots are discovered on disk, assigned per artist in `shot_assign.json`, and activated by the artist who owns them. The `/stage/shot{XXX}` nodes are bypassed and colour-coded automatically (black: not yours or missing on disk, red: yours, green: active).
- **Automatic Stage Setup:** Selecting a shot updates the live USD path of `/stage/shot_asb`, the `shot`, `shot_index` and `sequence` parameters of `/stage/LIGHTING_CTL`, and the Houdini timeline from the shot's `frame_range.json`.
- **Multi-Shot USD Writer:** Discovers the active SET and CHR layers of every shot, lets you set a frame range (or a single frame) per layer, configures the Cryptomatte output and triggers the `RDR_OUT_{layer}_{aov}` ROPs (Ci, Ut, Dp). Compute Extents nodes are temporarily bypassed during the export to avoid `extentsHint.timeSamples` bloat.
- **Modular PySide Front End:** A clean, artist-friendly UI architecture with a shared stylesheet, reusable collapsible shot / layer widgets, and Qt compatibility between PySide2 and PySide6.

## Usage
```python
from atlas_multishot import show_assignment_panel, show_selection_panel, show_write_panel

# Assign artists to the shots of the current sequence
show_assignment_panel()

# Pick the active shot among your assigned shots
show_selection_panel()

# Write the USD layers of several shots from the current scene
show_write_panel()
```

The sequence is read from the hip file name (`seq010sh020_light_v001.hipnc` or `seq010glb`), so a valid `seq###` hip file must be open.

### Data Files
| File                                    | Purpose                               |
|-----------------------------------------|---------------------------------------|
| `users.json`                            | Artist database (read-only)           |
| `$HIP/data/shot_assign.json`            | Shot assignments (read/write by tool) |
| `.../asb/houdini/live/frame_range.json` | Start / end frames of a shot          |

## License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

You are free to use, modify, and distribute this software under the terms of the GPL license.

See the full license text here: https://www.gnu.org/licenses/gpl-3.0.html

## Project Layout
```
atlas_multishot/
├── src/
│   └── atlas_multishot/      main python package root
│       ├── core/             Houdini-facing logic, zero UI dependencies
│       │   ├── utils/
│       │   │   ├── parse_sequence.py   hip file name → sequence / shot metadata
│       │   │   ├── scan_shot.py        shot discovery on disk
│       │   │   └── user_db.py          artist database and data file paths
│       │   ├── writer/
│       │   │   ├── bypass_extents.py   Compute Extents bypass context manager
│       │   │   ├── constants.py        storage roots, AOV suffixes, layer patterns
│       │   │   ├── execute.py          Cryptomatte and USD ROP execution
│       │   │   ├── hip_helpers.py      hip file helpers
│       │   │   └── layer_discovery.py  SET / CHR layer discovery
│       │   ├── assignment_manager.py   read / write shot_assign.json
│       │   └── stage_manager.py        /stage node states and parameters
│       ├── ui/               PySide front end
│       │   ├── stylesheet/
│       │   │   └── style.py  shared Atlas stylesheet
│       │   ├── writer/
│       │   │   ├── widget/
│       │   │   │   ├── layer_row.py       per-layer frame range row
│       │   │   │   ├── layer_subgroup.py  collapsible SET / CHR group
│       │   │   │   └── shot_panel.py      collapsible per-shot panel
│       │   │   └── main.py   multi-shot USD writer dialog
│       │   ├── assignment_ui.py  shot assignment dialog
│       │   └── selection_ui.py   shot selection dialog
│       └── __init__.py       public API
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## Contributing
Bug reports, feature requests, and PRs are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md) for branch/commit conventions and
where new code should live.

## Notes
Please ensure proper environment setup (Houdini 20.5, Python 3.11, PySide2 or PySide6) before running the tool inside the Andhakara asset pipeline. The tool relies on Atlas Manager (`Guard`) to resolve the logged-in artist and the project database, and expects the `/stage` network to contain the `shot{XXX}` nodes, `shot_asb`, `LIGHTING_CTL`, and the `CRYPTO_{layer}` and `RDR_OUT_{layer}_{aov}` nodes.
