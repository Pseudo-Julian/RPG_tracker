from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class StatRead(BaseModel):
    id: int
    code: str
    name:str
    description: str
    level: int
    current_xp: int
    xp_to_next_level: int = 100
    last_activity_date: Optional[date]

    model_config = ConfigDict(from_attributes=True)


class HabitCreate(BaseModel):
    title: str
    stat_code: str  # STR, INT, VIT, FOC
    difficulty: str = "medium"
    is_daily: bool = True


class HabitRead(BaseModel):
    id: int
    title: str
    stat_code: str
    difficulty: str
    base_xp: int
    streak: int
    is_daily: bool
    last_completed_date: Optional[date]
    completed_today: bool = False

    model_config = ConfigDict(from_attributes=True)


class QuestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    stat_code: str
    xp_reward: int = 150
    deadline: Optional[date] = None


class QuestRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    stat_code: str
    xp_reward: int
    deadline: Optional[date]
    is_completed: bool
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ActionLogRead(BaseModel):
    id: int
    action_type: str
    title: str
    stat_code: str
    xp_change: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class CharacterDashboard(BaseModel):
    name: str
    level: int
    total_xp: int
    hp: int
    max_hp: int
    stats: List[StatRead]
    recent_logs: List[ActionLogRead]