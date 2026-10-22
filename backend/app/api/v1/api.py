"""
CinemaAgent API v1 Router Module.
Exposes api_router with all endpoints mounted, including favorites.
"""
from fastapi import APIRouter
from app.api.v1.router import api_router

__all__ = ["api_router"]
