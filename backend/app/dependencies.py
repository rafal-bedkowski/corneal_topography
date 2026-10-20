from typing import cast

from fastapi import Request

from app.config import Settings
from app.store import IndexStore


def get_store(request: Request) -> IndexStore:
    return cast(IndexStore, request.app.state.store)


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)
