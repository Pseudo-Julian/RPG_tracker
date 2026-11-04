from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Character(Base):
    __tablename__ = "character"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Player")
    level = Column(Integer, default=1)
    total_xp = Column(Integer, default=0)
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    last_penalty_chek = Column(Date, default=date.today)


class Stat(Base):
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True) # STR, INT, VIT, FOC
    name = Column(String)
    description = Column(String)
    level = Column(Integer, default=1)
    current_xp = Column(Integer, default=0)
    last_activity_date = Column(Date, default=date.today)

    habits = relationship("Habit", back_populates="stat")
    quests = relationship("Quest", back_populates="stat")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    stat_code = Column(String, ForeignKey("stats.code"), nullable=False)
    difficulty = Column(String, default="medium") # easy, medium, hard
    base_xp = Column(Integer, default=25)
    streak = Column(Integer, default=0)
    is_daily = Column(Boolean, default=True)
    last_completed_date = Column(Date, nullable=True)
    created_at = Column(Date, default=date.today)

    stat = relationship("Stat", back_populates="habits")


class Quest(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stat_code = Column(String, ForeignKey("stats.code"), nullable=False)
    xp_reward = Column(Integer, default=150)
    deadline = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(Date, default=date.today)

    stat = relationship("Stat", back_populates="quests")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String)  # habit_done, quest_done, penalty_habit, penalty_decay
    title = Column(String)
    stat_code = Column(String)
    xp_change = Column(Integer)  # Може бути додатним (+25) або від'ємним (-20)
    timestamp = Column(DateTime, default=datetime.now)