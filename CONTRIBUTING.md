# Contributing to Atlas Multishot

Thanks for helping out. This is the lighting pipeline tool for the
*Andhakara* short, so changes should stay safe for artists mid-shot; see
below for what that means in practice.

## Before you start

Read the **Project Layout** section of [`README.md`](README.md). The one
rule that matters most: **`core` never imports from `ui`**. If a change
would require `core` to import PySide or a `ui` module, it belongs in
`ui` instead, calling into `core` for the Houdini-scene part.

## Branches & commits

- Branch from `main`: `feat/<short-name>`, `fix/<short-name>`,
  `docs/<short-name>`, `chore/<short-name>`.
- Commit messages: `type(scope): summary`, e.g.
  `fix(core.stage_manager): guard against a missing LIGHTING_CTL node`.
  Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`.
- Keep commits focused — a rename/move and a behavior change belong in
  separate commits so the diff is reviewable.

## Where new code goes

- `/stage` node states and parameters (`hou` calls) → `core/stage_manager.py`.
- Shot assignment persistence (`shot_assign.json`) → `core/assignment_manager.py`.
- Hip name parsing, shot discovery on disk, artist database → `core/utils/`.
- USD writing logic (layer discovery, Cryptomatte, USD ROPs, extents) → `core/writer/`.
- A new window/dialog → `ui/` (see `assignment_ui.py` and `selection_ui.py`).
- A reusable writer widget → `ui/writer/widget/`.
- Styling or shared constants → `ui/stylesheet/` (UI) or `core/writer/constants.py` (writer).

## Code style

- Every module starts with `# -*- coding: utf-8 -*-` and a docstring
  with a title, a short description and the `Author` / `Website` /
  `Created` block.
- Use Google-style docstrings (`Args:`, `Returns:`, `Raises:`) on every
  public class, function and method.
- Organise each module in `# region` / `# endregion` blocks separated by
  a `# ==========` line, starting with `# region Imports & Config`
  (imports grouped as python, pyside, dcc, atlas modules).

## Before opening a PR

```bash
ruff check .
black .
pytest
```

- Add or update a test in `tests/` for any `core` change (mock `hou`
  instead of importing it).
- Update `README.md` if you moved, renamed, or added a module — the
  project layout is the map new contributors use, and a stale map is
  worse than none.
- Keep the PR description focused on *why*, not just *what* — the diff
  already shows what changed.

## Reporting bugs / requesting features

Open an issue describing the problem or the feature. For anything that
could affect an in-progress shot (e.g. a change to the `shot_assign.json`
format, the `/stage` node naming, or the USD output paths in
`core/writer/constants.py`), please flag that explicitly in the issue or
PR so it can get extra review.

## Code of conduct

Be respectful and assume good faith — this is a small student/indie
production team, not a large open-source project, and most contributors
are also credited crew on the film.
