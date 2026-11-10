from datetime import date
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models, schemas, crud

# автоматичне створення таблиць при старті
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RPG Habit & Stat Tracker API", version="1.0.0")


@app.get("/dashboard", response_model=schemas.CharacterDashboard)
def read_dashboard(db: Session = Depends(get_db)):
    return crud.get_dashboard_data(db)


@app.post("/register", response_model=schemas.CharacterDashboard)
def register_hero(reg_in: schemas.CharacterRegister, db: Session = Depends(get_db)):
    crud.register_character(db, reg_in)
    return crud.get_dashboard_data(db)


@app.get("/habits", response_model=List[schemas.HabitRead])
def list_habits(db: Session = Depends(get_db)):
    crud.apply_daily_penalties(db)
    habits = db.query(models.Habit).all()
    today = date.today()
    result = []
    for h in habits:
        h_read = schemas.HabitRead.model_validate(h)
        h_read.completed_today = h.last_completed_date == today
        result.append(h_read)
    return result


@app.post("/habits", response_model=schemas.HabitRead)
def add_habit(habit_in: schemas.HabitCreate, db: Session = Depends(get_db)):
    return crud.create_habit(db, habit_in)


@app.post("/habits/{habit_id}/complete", response_model=schemas.HabitRead)
def mark_habit_done(habit_id: int, db: Session = Depends(get_db)):
    try:
        habit = crud.complete_habit(db, habit_id)
        h_read = schemas.HabitRead.model_validate(habit)
        h_read.completed_today = True
        return h_read
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter_by(id=habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Звичку не знайдено")
    db.delete(habit)
    db.commit()
    return {"status": "deleted"}


@app.get("/quests", response_model=List[schemas.QuestRead])
def list_quests(db: Session = Depends(get_db)):
    return db.query(models.Quest).order_by(models.Quest.is_completed.asc()).all()


@app.post("/quests", response_model=schemas.QuestRead)
def add_quest(quest_in: schemas.QuestCreate, db: Session = Depends(get_db)):
    return crud.create_quest(db, quest_in)


@app.post("/quests/{quest_id}/complete", response_model=schemas.QuestRead)
def mark_quest_done(quest_id: int, db: Session = Depends(get_db)):
    try:
        return crud.complete_quest(db, quest_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
