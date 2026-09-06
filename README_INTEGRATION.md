# Integration notes

## Files to add/replace

Add/replace only:

```text
entities/
README_ENTITIES.md
game.py
tests/test_entities.py
```

Do **not** replace `main.py`, `Renderer.py`, `audio.py`, `settings.py`, `menu/` or the existing assets.

## Why `game.py` changes

The current `main.py` already expects `CarreraDeObstaculos` and calls `reset_game`, `handle_events`, `update`, `draw`, `draw_gameover`, and `_update_record_summary`. The adapter preserves that interface while moving the actual card/domain logic into the new `entities/` package.

## Renderer boundary

The existing Renderer accepts dictionaries containing `rank`, `suit` and `selected`, so `CardEntity.to_dict()` provides those fields. The Renderer remains responsible for drawing. `CardFactory` creates and stores a `pygame.Rect` plus the expected asset path, but does not force the rest of the domain to import Pygame.

## Round reshuffle

A new round creates a fresh dynamic collection and calls `shuffle()`. Future packages can instead change the collection size or insert duplicate cards before shuffling.
