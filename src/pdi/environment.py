"""Backward-compat shim. Real environments live in `pdi.environments.*`.

Kept so existing tests/imports (`from pdi.environment import Environment`)
continue to work. The default `Environment` alias is the random-respawn
GridWorldEnvironment.
"""
from __future__ import annotations

from .environments import GridWorldEnvironment as Environment
from .environments.base import Tile

__all__ = ["Environment", "Tile"]
