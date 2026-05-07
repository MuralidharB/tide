from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from tide.db import connect
from tide.watchlist.compute import compute_watchlist

router = APIRouter()


class WatchlistRowOut(BaseModel):
    ticker: str
    name: str
    sub: str
    price: float | None
    target: float
    fwd_pe: str
    status: str
    return_30d: float | None
    return_30d_relative: float | None
    sparkline: list[float]
    as_of: date | None


class WatchlistOut(BaseModel):
    rows: list[WatchlistRowOut]
    benchmark: str


@router.get("/watchlist", response_model=WatchlistOut)
def get_watchlist() -> WatchlistOut:
    with connect(read_only=True) as conn:
        rows = compute_watchlist(conn)
    return WatchlistOut(
        rows=[WatchlistRowOut(**row.__dict__) for row in rows],
        benchmark="XLV",
    )
