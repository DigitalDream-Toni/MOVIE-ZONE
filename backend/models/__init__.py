from pydantic import BaseModel
from typing import Optional, List


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class MovieCreate(BaseModel):
    title: str
    year: Optional[int] = None
    description: Optional[str] = ""
    genre: Optional[str] = ""
    poster: Optional[str] = ""
    backdrop: Optional[str] = ""
    download_url: Optional[str] = ""
    watch_url: Optional[str] = None
    is_featured: Optional[bool] = False


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    poster: Optional[str] = None
    backdrop: Optional[str] = None
    download_url: Optional[str] = None
    watch_url: Optional[str] = None
    is_featured: Optional[bool] = None


class EpisodeCreate(BaseModel):
    episode_number: int
    title: str
    description: Optional[str] = ""
    download_url: Optional[str] = ""
    watch_url: Optional[str] = None


class SeasonCreate(BaseModel):
    season_number: int
    title: Optional[str] = None
    episodes: Optional[List[EpisodeCreate]] = []


class SeriesCreate(BaseModel):
    title: str
    year: Optional[int] = None
    description: Optional[str] = ""
    genre: Optional[str] = ""
    poster: Optional[str] = ""
    backdrop: Optional[str] = ""
    seasons: Optional[List[SeasonCreate]] = []


class SeriesUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    poster: Optional[str] = None
    backdrop: Optional[str] = None
    seasons: Optional[List[SeasonCreate]] = None
