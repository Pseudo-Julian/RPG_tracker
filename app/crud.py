from datetime import date, datetime
from sqlalchemy.orm import Session
from app import models, schemas


DIFFICULTY_XP = {
    "easy": 10,
    "medium": 25,
    "hard": 50,
}

DEFAULT_STATS = [
    {"code": "STR", "name": "Strength", "description": "Тренування та фізична форма"},
    {"code": "INT", "name": "Intelligence", "description": "Навчання, розвиток, мови"},
    {"code": "VIT", "name": "Vitality", "description": "Сон, харчування, здоров'я"},
    {"code": "FOC", "name": "Focus", "description": "Дисципліна, рутина, фокус"},
]


def xp_for_next_level(level: int) -> int:
    return int(100 * (level ** 1.5))

def recalculate_character_level(db: Session, char: models.Character):
    """Загальний рівень персонажа = сер. арифметичне всіх рівнів stats"""
    stats = db.query(models.Stat).all()
    if stats:
        char.level = sum(s.level for s in stats) // len(stats)

def init_character_and_stats(db: Session) -> models.Character:
    """Create unit and base stats"""
    char = db.query(models.Character).first()
    if not char:
        char = models.Character(
            name="Player",
            level=1,
            total_xp=0,
            hp=100,
            max_hp=100,
            last_penalty_chek=date.today(),
        )
        db.add(char)
        db.commit()
        db.refresh(char)

    for s_data in DEFAULT_STATS:
        stat = db.query(models.Stat).filter_by(code=s_data["code"]).first()
        if not stat:
            stat = models.Stat(
                code=s_data["code"],
                name=s_data["name"],
                description=s_data["description"],
                level=1,
                current_xp=0,
                last_activity_date=date.today(),
            )
            db.add(stat)
    db.commit()
    return char

def modify_stat_xp(
    db: Session,
    stat: models.Stat,
    xp_delta: int,
    action_type: str,
    title: str,
    update_activity_date: bool = True,
):
    """Додає або мінусує XP зі stat з підтримкою Lev-Up та Hardcore De_Lev"""
    char = db.query(models.Character).first()
    stat.current_xp += xp_delta

    if xp_delta > 0:
        char.total_xp += xp_delta
        if update_activity_date:
            stat.last_activity_date = date.today()

        # check for Level_up
        while stat.current_xp >= xp_for_next_level(stat.level):
            stat.current_xp -= xp_for_next_level(stat.level)
            stat.level += 1
            char.hp = min(char.max_hp, char.hp +10) # Бонус +10 HP за новий рівень

    elif xp_delta < 0:
        char.total_xp = max(0, char.total_xp + xp_delta)
        char.hp = max(1, char.hp - 5)  # Втрата HP за штраф

        while stat.current_xp < 0:
            if stat.level > 1:
                stat.level -= 1
                stat.current_xp += xp_for_next_level(stat.level)
            else:
                stat.current_xp = 0
                break

    recalculate_character_level(db, char)

    log = models.ActionLog(
        action_type=action_type,
        title=title,
        stat_code=stat.code,
        xp_change=xp_delta,
        timestamp=datetime.now(),
    )
    db.add(log)
    db.commit()

def apply_daily_penalties(db: Session):
    """Перевіряє пропуски > 1 дня для daily task та загальний простій stats"""
    char = init_character_and_stats(db)
    today = date.today()

    if char.last_penalty_chek >= today:
        return

    habits = db.query(models.Habit).filter_by(is_daily=True).all()
    for habit in habits:
        ref_date = habit.last_completed_date or habit.created_at
        days_missed = (today - ref_date).days - 1

        if days_missed > 0:
            habit.streak = 0
            penalty_per_day = max(5, habit.base_xp // 2)
            total_penalty = -(penalty_per_day * days_missed)
            stat = db.query(models.Stat).filter_by(code=habit.stat_code).first()
            if stat:
                modify_stat_xp(
                    db,
                    stat,
                    total_penalty,
                    action_type="penalty_habit",
                    title=f"Пропуск звички ({days_missed} дн.): {habit.title}",
                    update_activity_date=False,
                )
    char.last_penalty_check = today
    db.commit()

def create_habit(db: Session, habit_in: schemas.HabitCreate) -> models.Habit:
    base_xp = DIFFICULTY_XP.get(habit_in.difficulty.lower(), 25)
    habit = models.Habit(
        title=habit_in.title,
        stat_code=habit_in.stat_code.upper(),
        difficulty=habit_in.difficulty.lower(),
        base_xp=base_xp,
        is_daily=habit_in.is_daily,
        created_at=date.today(),
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit

def complete_habit(db: Session, habit_id: int) -> models.Habit:
    habit = db.query(models.Habit).filter_by(id=habit_id).first()
    if not habit:
        raise ValueError("Звичка не знайдена")

    today = date.today()
    if habit.last_completed_date == today:
        raise ValueError("Ця звичка виконана сьогодні")

    # Перевірка на streak
    if habit.last_completed_date and (today - habit.last_completed_date).days <= 2:
        habit.streak += 1
    else:
        habit.streak = 1

    habit.last_completed_date = today

    # Бонус за streak: + 5% за кожен день серії (max +50%)
    streak_multiplier = min(0.50, (habit.streak - 1) * 0.05)
    earned_xp = int(habit.base_xp * (1.0 + streak_multiplier))

    stat = db.query(models.Stat).filter_by(code=habit.stat_code).first()
    modify_stat_xp(
        db,
        stat,
        earned_xp,
        action_type="habit_done",
        title=f"{habit.title} (Стрік: {habit.streak})",
        update_activity_date=True,
    )
    db.commit()
    db.refresh(habit)
    return habit

def create_quest(db: Session, quest_in: schemas.QuestCreate) -> models.Quest:
    quest = models.Quest(
        title=quest_in.title,
        description=quest_in.description,
        stat_code=quest_in.stat_code.upper(),
        xp_reward=quest_in.xp_reward,
        deadline=quest_in.deadline,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)
    return quest

def complete_quest(db: Session, quest_id: int) -> models.Quest:
    quest = db.query(models.Quest).filter_by(id=quest_id).first()
    if not quest:
        raise ValueError("Квест не знайдено")
    if quest.is_completed:
        raise ValueError("Квест вже виконано!")

    quest.is_completed = True
    quest.completed_at = datetime.now()

    stat = db.query(models.Stat).filter_by(code=quest.stat_code).first()
    modify_stat_xp(
        db,
        stat,
        quest.xp_reward,
        action_type="quest_done",
        title=f"Квест: {quest.title}",
        update_activity_date=True,
    )
    db.commit()
    db.refresh(quest)
    return quest

def get_dashboard_data(db: Session) -> schemas.CharacterDashboard:
    apply_daily_penalties(db)
    char = db.query(models.Character).first()
    stats = db.query(models.Stat).all()
    logs = (
        db.query(models.ActionLog)
        .order_by(models.ActionLog.timestamp.desc())
        .limit(15)
        .all()
    )

    stat_reads = []
    for s in stats:
        s_read = schemas.StatRead.model_validate(s)
        s_read.xp_to_next_level = xp_for_next_level(s.level)
        stat_reads.append(s_read)

    return schemas.CharacterDashboard(
        name=char.name,
        level=char.level,
        total_xp=char.total_xp,
        hp=char.hp,
        max_hp=char.max_hp,
        stats=stat_reads,
        recent_logs=[schemas.ActionLogRead.model_validate(l) for l in logs],
    )
