
from typing import List

from pydantic import BaseModel, Field


class Activity(BaseModel):
    time: str = Field(description="Approximate time of the activity")
    title: str = Field(description="Activity or place to visit")
    description: str = Field(description="What the traveler can do")
    estimated_cost: float | None = Field(
        default=None,
        ge=0,
        description="Estimated cost in the trip's currency",
    )


class DayPlan(BaseModel):
    day: int = Field(ge=1)
    date: str | None = None
    title: str
    activities: List[Activity] = Field(min_length=1)


class HotelRecommendation(BaseModel):
    name: str
    location: str | None = None
    estimated_price_per_night: float | None = Field(default=None, ge=0)
    source: str | None = None


class TravelItinerary(BaseModel):
    destination: str
    duration_days: int = Field(ge=1)
    currency: str = "INR"
    overview: str
    daily_plans: List[DayPlan] = Field(min_length=1)
    hotels: List[HotelRecommendation] = Field(default_factory=list)
    estimated_total_budget: float | None = Field(default=None, ge=0)
    weather_advice: str
    practical_tips: List[str] = Field(default_factory=list)
