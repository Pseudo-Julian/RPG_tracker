import os
from datetime import datetime
from PIL import Image, ImageEnhance
import requests
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

STAT_COLORS = {
    "STR": "#e74c3c",
    "INT": "#3498db",
    "VIT": "#2ecc71",
    "FOC": "#9b59b6",
}

ARCHETYPES = [
    {
        "code": "STR",
        "perk": "Шлях Сили (+20% STR)",
        "title": "Авангард Залізного Кулака",
        "lore": (
            "«Тіло — твоя перша фортеця, а піт на тренуванні береже кров у бою. "
            "Обери цей шлях, якщо прагнеш кувати незламну фізичну міць щодня — "
            "а далі все у твоїх руках!»"
        ),
    },
    {
        "code": "INT",
        "perk": "Шлях Розуму (+20% INT)",
        "title": "Магістр Таємних Знань",
        "lore": (
            "«Мечі тупляться, але гострий розум розтинає будь-яку темряву. "
            "Шлях для тих, хто приборкує код, науки та чужоземні мови — "
            "а далі все у твоїх руках!»"
        ),
    },
    {
        "code": "VIT",
        "perk": "Шлях Життя (+20% VIT)",
        "title": "Вартовий Смарагдового Ордену",
        "lore": (
            "«Навіть найвеличніший воїн впаде без глибокого сну та чистої поживи. "
            "Обери гармонію здоров'я, відновлення та витривалості — "
            "а далі все у твоїх руках!»"
        ),
    },
    {
        "code": "FOC",
        "perk": "Шлях Волі (+20% FOC)",
        "title": "Інквізитор Залізної Волі",
        "lore": (
            "«Хаос відступає перед тим, хто володіє власною увагою та рутиною. "
            "Холодний фокус і щоденна дисципліна приведуть тебе на вершину — "
            "а далі все у твоїх руках!»"
        ),
    },
]

# Кеш для зображень 2048x2048, щоб перемикання M/W працювало миттєво
_SPRITE_CACHE: dict[tuple[str, tuple[int, int]], ctk.CTkImage] = {}


def load_pixel_sprite(filename: str, size: tuple[int, int]) -> ctk.CTkImage | None:
    """Завантажує портрет 2048x2048 з ui/assets/, прибирає фон (якщо є) і масштабує на весь квадрат."""
    cache_key = (filename, size)
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]

    path = os.path.join(os.path.dirname(__file__), "assets", filename)
    if not os.path.exists(path):
        return None

    pil_img = Image.open(path).convert("RGBA")

    # Якщо кутовий піксель непрозорий, автоматично робимо однотонний фон прозорим
    bg_r, bg_g, bg_b, bg_a = pil_img.getpixel((0, 0))
    if bg_a > 0:
        # Спочатку зменшуємо до цільового розміру для миттєвої обробки пікселів
        pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
        datas = pil_img.getdata()
        tolerance = 22
        new_data = [
            (255, 255, 255, 0)
            if (
                abs(r - bg_r) <= tolerance
                and abs(g - bg_g) <= tolerance
                and abs(b - bg_b) <= tolerance
            )
            else (r, g, b, a)
            for r, g, b, a in datas
        ]
        pil_img.putdata(new_data)
    else:
        pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)

    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    _SPRITE_CACHE[cache_key] = ctk_img
    return ctk_img

def load_medal_sprite(
    filename: str, size: tuple[int, int] = (54, 54), locked: bool = False
) -> ctk.CTkImage | None:
    """Завантажує медаль, вирізає фон, а для locked=True робить темний силует із ледь видимою текстурою."""
    cache_key = (f"medal_{filename}_{locked}", size)
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]

    medals_dir = os.path.join(os.path.dirname(__file__), "assets", "medals")
    os.makedirs(medals_dir, exist_ok=True)
    base_name = os.path.splitext(filename)[0]

    path = None
    for ext in (".png", ".jpg", ".jpeg"):
        candidate = os.path.join(medals_dir, base_name + ext)
        if os.path.exists(candidate):
            path = candidate
            break

    if not path:
        return None

    clean_key = (f"medal_clean_pil_{base_name}", (512, 512))
    if clean_key in _SPRITE_CACHE:
        pil_img = _SPRITE_CACHE[clean_key].copy()
    else:
        pil_img = Image.open(path).convert("RGBA")
        pil_img = pil_img.resize((512, 512), Image.Resampling.LANCZOS)

        w, h = pil_img.size
        px = pil_img.load()
        bg_r, bg_g, bg_b, bg_a = px[0, 0]

        if bg_a > 0:
            tolerance = 32
            visited = set()
            stack = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]

            while stack:
                x, y = stack.pop()
                if (x, y) in visited or not (0 <= x < w and 0 <= y < h):
                    continue
                visited.add((x, y))

                r, g, b, a = px[x, y]
                if (
                    abs(r - bg_r) <= tolerance
                    and abs(g - bg_g) <= tolerance
                    and abs(b - bg_b) <= tolerance
                ):
                    px[x, y] = (0, 0, 0, 0)
                    stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

        _SPRITE_CACHE[clean_key] = pil_img.copy()

    # Якщо медаль ще не здобута — знебарвлюємо і сильно затемнюємо текстуру, зберігаючи контур (alpha)
    if locked:
        r, g, b, alpha = pil_img.split()
        gray = pil_img.convert("L")
        dark_gray = ImageEnhance.Brightness(gray).enhance(0.18)  # 18% яскравості (темний силует)
        pil_img = Image.merge("RGBA", (dark_gray, dark_gray, dark_gray, alpha))

    pil_resized = pil_img.resize(size, Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=pil_resized, dark_image=pil_resized, size=size)
    _SPRITE_CACHE[cache_key] = ctk_img
    return ctk_img


ALL_MEDALS_INFO = [
    ("lvl_10", "Рівень 10", "Досягнуто 10 загального рівня", "lvl_10.png"),
    ("lvl_20", "Рівень 20", "Досягнуто 20 загального рівня", "lvl_20.png"),
    ("lvl_50", "Рівень 50", "Досягнуто 50 загального рівня", "lvl_50.png"),
    ("lvl_100", "Рівень 100", "Досягнуто 100 загального рівня", "lvl_100.png"),
    ("lvl_200", "Рівень 200", "Досягнуто 200 загального рівня", "lvl_200.png"),
    ("str_20", "STR 20", "Сила досягла 20 рівня", "str_20.png"),
    ("int_20", "INT 20", "Інтелект досяг 20 рівня", "int_20.png"),
    ("vit_20", "VIT 20", "Здоров'я досягло 20 рівня", "vit_20.png"),
    ("foc_20", "FOC 20", "Фокус досяг 20 рівня", "foc_20.png"),
    ("str_100", "STR 100", "Сила досягла 100 рівня", "str_100.png"),
    ("int_100", "INT 100", "Інтелект досяг 100 рівня", "int_100.png"),
    ("vit_100", "VIT 100", "Здоров'я досягло 100 рівня", "vit_100.png"),
    ("foc_100", "FOC 100", "Фокус досяг 100 рівня", "foc_100.png"),
    ("no_penalty_50", "50 днів без штрафів", "50 днів дисципліни без пропусків", "no_penalty_50.png"),
    ("no_penalty_100", "100 днів без штрафів", "100 днів залізної дисципліни", "no_penalty_100.png"),
    ("lost_level", "Ціна простою", "Втрачено рівень характеристики через пропуски", "lost_level.png"),
]


class MedalUnlockPopup(ctk.CTkToplevel):
    """Вікно огляду медалі (святкове для відкритої або затемнений силует для закритої)."""

    def __init__(self, parent: "RPGTrackerApp", achievement: dict, is_unlocked: bool = True):
        super().__init__(parent)
        self.title("Нове Досягнення!" if is_unlocked else "Таємний Трофей (Закрито)")
        w, h = 460, 480

        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        border_col = "#d4af37" if is_unlocked else "#3a3d45"
        card = ctk.CTkFrame(
            self, corner_radius=16, fg_color="#181a20", border_width=2, border_color=border_col
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        header_text = "✨ ВІТАЄМО! НОВА МЕДАЛЬ ✨" if is_unlocked else "🔒 ТРОФЕЙ ЩЕ НЕ ЗДОБУТО"
        header_col = "#d4af37" if is_unlocked else "#6c727f"

        ctk.CTkLabel(
            card,
            text=header_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=header_col,
        ).pack(pady=(20, 10))

        # Велике зображення медалі 220x220 (затемнене, якщо ще не відкрита)
        img = load_medal_sprite(achievement["sprite"], (220, 220), locked=not is_unlocked)
        if img:
            ctk.CTkLabel(card, image=img, text="", fg_color="transparent").pack(pady=8)
        else:
            ctk.CTkLabel(
                card, text="🏅" if is_unlocked else "🔒", font=ctk.CTkFont(size=96)
            ).pack(pady=15)

        ctk.CTkLabel(
            card,
            text=achievement["title"].upper(),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ffffff" if is_unlocked else "#7f8c8d",
        ).pack(pady=(10, 4))

        ctk.CTkLabel(
            card,
            text=achievement["description"],
            font=ctk.CTkFont(size=14),
            text_color="#b0b5c0" if is_unlocked else "#6c727f",
            wraplength=380,
        ).pack(pady=(0, 18))

        ctk.CTkButton(
            card,
            text="Прийняти нагороду" if is_unlocked else "Закрити",
            width=200,
            height=42,
            corner_radius=10,
            fg_color="#b8860b" if is_unlocked else "#3a3d45",
            hover_color="#d4af37" if is_unlocked else "#50545e",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.destroy,
        ).pack(pady=(0, 18))


class MedalsGalleryWindow(ctk.CTkToplevel):
    """Вікно перегляду всіх медалей: відкриті сяють, закриті — темні силуети з обрисами."""

    def __init__(self, parent: "RPGTrackerApp", unlocked_list: list[dict]):
        super().__init__(parent)
        self.title("Зала Слави — Всі Медалі та Досягнення")
        w, h = 1080, 740
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")
        self.minsize(960, 620)

        self.transient(parent)
        self.grab_set()

        unlocked_map = {a["code"]: a for a in unlocked_list}

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(18, 8))

        ctk.CTkLabel(
            top_bar,
            text=f"🏅 ЗАЛА СЛАВИ ТА ДОСЯГНЕНЬ ({len(unlocked_map)} / {len(ALL_MEDALS_INFO)})",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#d4af37",
        ).pack(side="left")

        ctk.CTkLabel(
            top_bar,
            text="Невідкриті медалі приховані в тіні — виконайте умови, щоб відкрити їх",
            font=ctk.CTkFont(size=13),
            text_color="#888e99",
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self, corner_radius=12, fg_color="#14161b")
        scroll.pack(fill="both", expand=True, padx=24, pady=(4, 20))
        for col in range(4):
            scroll.grid_columnconfigure(col, weight=1)

        for idx, (code, title, desc, sprite_file) in enumerate(ALL_MEDALS_INFO):
            row, col = divmod(idx, 4)
            is_unlocked = code in unlocked_map
            ach_data = unlocked_map.get(
                code, {"code": code, "title": title, "description": desc, "sprite": sprite_file}
            )

            card = ctk.CTkFrame(
                scroll,
                corner_radius=12,
                fg_color="#20232b" if is_unlocked else "#17191f",
                border_width=2 if is_unlocked else 1,
                border_color="#d4af37" if is_unlocked else "#2c303a",
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Передаємо locked=not is_unlocked для затемнення невідкритих медалей
            img = load_medal_sprite(sprite_file, (135, 135), locked=not is_unlocked)
            if img:
                btn_img = ctk.CTkButton(
                    card,
                    image=img,
                    text="",
                    fg_color="transparent",
                    hover_color="#2a2e38" if is_unlocked else "#1e2028",
                    width=145,
                    height=145,
                    command=lambda a=ach_data, u=is_unlocked: MedalUnlockPopup(parent, a, is_unlocked=u),
                )
                btn_img.pack(pady=(14, 6))
            else:
                ctk.CTkLabel(
                    card,
                    text="🏅" if is_unlocked else "🔒",
                    font=ctk.CTkFont(size=54),
                ).pack(pady=(20, 10))

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#d4af37" if is_unlocked else "#6c727f",
            ).pack(padx=10, pady=(2, 2))

            ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color="#cccccc" if is_unlocked else "#555a66",
                wraplength=210,
                justify="center",
            ).pack(padx=10, pady=(0, 6))

            if is_unlocked:
                dt_str = datetime.fromisoformat(ach_data["unlocked_at"]).strftime("%d.%m.%Y")
                status_text = f"✓ Здобуто: {dt_str}"
                status_color = "#2ecc71"
            else:
                status_text = "🔒 Ще не відкрито"
                status_color = "#555a66"

            ctk.CTkLabel(
                card,
                text=status_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=status_color,
            ).pack(pady=(0, 12))


class RegistrationWindow(ctk.CTkToplevel):
    """Збільшене вікно створення персонажа (квадрати портретів 250x250 на весь блок)."""

    CARD_IMG_SIZE = (250, 250)

    def __init__(self, parent: "RPGTrackerApp", current_name: str = ""):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Створення Персонажа — Оберіть свій Шлях")
        self.geometry("1260x760")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.selected_stat = "STR"
        self.card_genders = {"STR": "M", "INT": "M", "VIT": "M", "FOC": "M"}
        self.cards_ui = {}

        self._build_ui(current_name)
        self._update_selection_visuals()

    def _build_ui(self, current_name: str):
        # 1. Верхній ряд: поле "Введіть ім'я"
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=25, pady=(20, 10))

        self.entry_name = ctk.CTkEntry(
            top_bar,
            placeholder_text="Введіть ім'я лицаря...",
            width=380,
            height=46,
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=8,
        )
        self.entry_name.pack(side="left")
        if current_name and current_name != "Player":
            self.entry_name.insert(0, current_name)

        ctk.CTkLabel(
            top_bar,
            text="Оберіть головну особливість (+20% до XP обраного стату) та стать (M / W):",
            font=ctk.CTkFont(size=14),
            text_color="#a0a0a0",
        ).pack(side="right", padx=10)

        # 2. Середній ряд: 4 великі картки персонажів
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="both", expand=True, padx=20, pady=10)
        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)
        cards_container.grid_rowconfigure(0, weight=1)

        for idx, arch in enumerate(ARCHETYPES):
            code = arch["code"]
            color = STAT_COLORS[code]

            col_frame = ctk.CTkFrame(cards_container, corner_radius=14, border_width=2)
            col_frame.grid(row=0, column=idx, padx=8, pady=5, sticky="nsew")

            # Рамка "Особливість" зверху над зображенням
            perk_box = ctk.CTkFrame(
                col_frame,
                fg_color="#1e1e1e",
                corner_radius=8,
                border_width=1,
                border_color=color,
            )
            perk_box.pack(fill="x", padx=12, pady=(14, 10))

            lbl_perk = ctk.CTkLabel(
                perk_box,
                text=arch["perk"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=color,
            )
            lbl_perk.pack(pady=8)

            # Великий квадрат (250x250), де зображення лицаря займає 100% площі
            img_box = ctk.CTkFrame(
                col_frame,
                width=self.CARD_IMG_SIZE[0],
                height=self.CARD_IMG_SIZE[1],
                corner_radius=10,
                fg_color="#14161b",
                border_width=1,
                border_color="#2f333d",
            )
            img_box.pack(padx=12, pady=6)
            img_box.pack_propagate(False)

            sprite = load_pixel_sprite(f"{code.lower()}_m.png", self.CARD_IMG_SIZE)
            btn_avatar = ctk.CTkButton(
                img_box,
                text="" if sprite else code,
                image=sprite,
                width=self.CARD_IMG_SIZE[0],
                height=self.CARD_IMG_SIZE[1],
                corner_radius=0,
                border_spacing=0,
                fg_color="transparent",
                hover_color="#222630",
                command=lambda c=code: self.select_archetype(c),
            )
            btn_avatar.pack(fill="both", expand=True, padx=2, pady=2)

            # Назва ордену під картинкою
            ctk.CTkLabel(
                col_frame,
                text=arch["title"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#cccccc",
            ).pack(pady=(6, 6))

            # Кнопки M / W знизу під кожним зображенням
            mw_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            mw_frame.pack(pady=(4, 14))

            btn_m = ctk.CTkButton(
                mw_frame,
                text="M",
                width=64,
                height=36,
                font=ctk.CTkFont(size=15, weight="bold"),
                command=lambda c=code: self.set_card_gender(c, "M"),
            )
            btn_m.pack(side="left", padx=8)

            btn_w = ctk.CTkButton(
                mw_frame,
                text="W",
                width=64,
                height=36,
                font=ctk.CTkFont(size=15, weight="bold"),
                command=lambda c=code: self.set_card_gender(c, "W"),
            )
            btn_w.pack(side="left", padx=8)

            self.cards_ui[code] = {
                "frame": col_frame,
                "img_box": img_box,
                "avatar_btn": btn_avatar,
                "btn_m": btn_m,
                "btn_w": btn_w,
                "arch": arch,
            }

        # 3. Нижній блок: Короткий опис в середньовічному стилі + кнопка старту
        bottom_box = ctk.CTkFrame(
            self, corner_radius=12, border_width=1, border_color="#555555"
        )
        bottom_box.pack(fill="x", padx=25, pady=(8, 22))

        self.btn_confirm = ctk.CTkButton(
            bottom_box,
            text="⚔️\nВ ПУТЬ",
            width=95,
            height=85,
            corner_radius=45,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.confirm_registration,
        )
        self.btn_confirm.pack(side="left", padx=20, pady=15)

        self.lbl_lore = ctk.CTkLabel(
            bottom_box,
            text="",
            font=ctk.CTkFont(size=16, slant="italic"),
            wraplength=1040,
            justify="left",
            text_color="#e0e0e0",
        )
        self.lbl_lore.pack(side="left", padx=15, pady=15, fill="x", expand=True)

    def select_archetype(self, stat_code: str):
        self.selected_stat = stat_code
        self._update_selection_visuals()

    def set_card_gender(self, stat_code: str, gender: str):
        self.card_genders[stat_code] = gender
        self.selected_stat = stat_code

        filename = f"{stat_code.lower()}_{gender.lower()}.png"
        new_sprite = load_pixel_sprite(filename, self.CARD_IMG_SIZE)
        if new_sprite:
            self.cards_ui[stat_code]["avatar_btn"].configure(image=new_sprite)

        self._update_selection_visuals()

    def _update_selection_visuals(self):
        for code, ui in self.cards_ui.items():
            is_selected = code == self.selected_stat
            color = STAT_COLORS[code]

            ui["frame"].configure(
                border_color=color if is_selected else "#333333",
                fg_color="#262932" if is_selected else "#1f2128",
            )
            ui["img_box"].configure(
                border_color=color if is_selected else "#2f333d",
                border_width=2 if is_selected else 1,
            )

            g = self.card_genders[code]
            ui["btn_m"].configure(
                fg_color=color if g == "M" else "#3a3a3a",
                hover_color=color,
            )
            ui["btn_w"].configure(
                fg_color=color if g == "W" else "#3a3a3a",
                hover_color=color,
            )

            if is_selected:
                self.lbl_lore.configure(text=ui["arch"]["lore"])

    def confirm_registration(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Ім'я героя", "Введіть своє ім'я перед початком шляху!")
            return

        chosen_gender = self.card_genders[self.selected_stat]
        payload = {
            "name": name,
            "primary_stat": self.selected_stat,
            "gender": chosen_gender,
        }
        try:
            resp = self.parent_app.http.post(
                f"{self.parent_app.api_url}/register", json=payload, timeout=10
            )
            resp.raise_for_status()
            self.parent_app.refresh_all()
            self.destroy()
        except requests.RequestException as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти персонажа:\n{e}")


class RPGTrackerApp(ctk.CTk):
    """Збільшене головне вікно з великим портретом персонажа 125x125."""

    HEADER_AVATAR_SIZE = (188, 188)

    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
        self.http = requests.Session()
        self.http.headers.update({"Connection": "close"})
        self.reg_window_opened = False
        self.known_achievements: set[str] | None = None
        self.current_achievements: list[dict] = []

        self.title("RPG Habit & Stat Tracker")
        self.geometry("1320x840")
        self.minsize(1150, 740)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(self, corner_radius=14)
        self.header_frame.grid(
            row=0, column=0, columnspan=2, padx=18, pady=(18, 10), sticky="ew"
        )
        self._setup_header()

        self.stats_frame = ctk.CTkFrame(self, corner_radius=14)
        self.stats_frame.grid(row=1, column=0, padx=(18, 10), pady=(8, 18), sticky="nsew")
        self.stat_widgets = {}
        self._setup_stats_panel()

        self.tabview = ctk.CTkTabview(self, corner_radius=14)
        self.tabview.grid(row=1, column=1, padx=(10, 18), pady=(8, 18), sticky="nsew")

        self.tab_habits = self.tabview.add("Звички (Dailies)")
        self.tab_quests = self.tabview.add("Квести (Цілі)")
        self.tab_logs = self.tabview.add("Історія (Logs)")

        self._setup_habits_tab()
        self._setup_quests_tab()
        self._setup_logs_tab()

        self.refresh_all()

    def _setup_header(self):
        # 2 рядки справа від портрета: 0 — інфо та HP, 1 — широка вітрина медалей
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_rowconfigure(0, weight=0)
        self.header_frame.grid_rowconfigure(1, weight=1)

        # Портрет 188x188 займає обидва рядки по висоті (rowspan=2)
        self.avatar_box = ctk.CTkFrame(
            self.header_frame,
            width=self.HEADER_AVATAR_SIZE[0],
            height=self.HEADER_AVATAR_SIZE[1],
            corner_radius=0,
            fg_color="#181a20",
            border_width=2,
            border_color="#3a3d45",
        )
        self.avatar_box.grid(
            row=0, column=0, rowspan=2, padx=(18, 16), pady=12, sticky="ns"
        )
        self.avatar_box.pack_propagate(False)

        self.lbl_avatar = ctk.CTkLabel(
            self.avatar_box,
            text="⚔️",
            font=ctk.CTkFont(size=56),
            fg_color="transparent",
            corner_radius=0,
        )
        self.lbl_avatar.pack(fill="both", expand=True, padx=0, pady=0)

        # --- ВЕРХНЯ ПОЛОВИНА БАРУ (row=0) ---
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=1, padx=4, pady=(14, 4), sticky="nw")

        self.lbl_char_title = ctk.CTkLabel(
            title_box,
            text="PLAYER | РІВЕНЬ 1",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.lbl_char_title.pack(anchor="w")

        self.lbl_char_perk = ctk.CTkLabel(
            title_box,
            text="Бонус класу: +20% STR XP",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c",
        )
        self.lbl_char_perk.pack(anchor="w", pady=(2, 0))

        self.lbl_total_xp = ctk.CTkLabel(
            self.header_frame,
            text="Загальний досвід: 0 XP",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#a0a0a0",
        )
        self.lbl_total_xp.grid(row=0, column=2, padx=20, pady=(20, 4), sticky="nw")

        ctk.CTkButton(
            self.header_frame,
            text="⚙ Персонаж",
            width=120,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3a3d45",
            hover_color="#50545e",
            command=lambda: RegistrationWindow(self, self.current_hero_name),
        ).grid(row=0, column=3, padx=12, pady=(16, 4), sticky="ne")

        hp_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        hp_box.grid(row=0, column=4, padx=(12, 22), pady=(14, 4), sticky="ne")

        self.lbl_hp = ctk.CTkLabel(
            hp_box,
            text="HP: 100 / 100",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#ff6b6b",
        )
        self.lbl_hp.pack(anchor="e")

        self.hp_bar = ctk.CTkProgressBar(
            hp_box, width=210, height=14, progress_color="#e74c3c"
        )
        self.hp_bar.pack(pady=(6, 0))
        self.hp_bar.set(1.0)

        # --- НИЖНЯ ПОЛОВИНА БАРУ (row=1): Широке вікно для медалей та досягнень ---
        self.medals_frame = ctk.CTkFrame(
            self.header_frame,
            height=96,
            corner_radius=10,
            fg_color="#181a20",
            border_width=1,
            border_color="#2f333d",
        )
        self.medals_frame.grid(
            row=1, column=1, columnspan=4, padx=(4, 22), pady=(4, 12), sticky="nsew"
        )
        self.medals_frame.pack_propagate(False)

        medals_header = ctk.CTkFrame(self.medals_frame, fg_color="transparent")
        medals_header.pack(fill="x", padx=12, pady=(6, 2))

        ctk.CTkLabel(
            medals_header,
            text="🏅 МЕДАЛІ ТА ДОСЯГНЕННЯ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#7f8c8d",
        ).pack(side="left")

        # Контейнер, куди ми будемо динамічно додавати іконки медалей
        self.medals_slots_box = ctk.CTkFrame(self.medals_frame, fg_color="transparent")
        self.medals_slots_box.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self.lbl_no_medals = ctk.CTkLabel(
            self.medals_slots_box,
            text="Поки немає відкритих трофеїв — виконуйте звички та здобувайте рівні",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="#555a66",
        )
        self.lbl_no_medals.pack(side="left", pady=4)

        # Робимо всю панель медалей клікабельною для відкриття великої галереї
        self.medals_frame.configure(cursor="hand2")
        self.medals_frame.bind("<Button-1>", lambda e: self.open_medals_gallery())
        self.medals_slots_box.bind("<Button-1>", lambda e: self.open_medals_gallery())

    def open_medals_gallery(self):
        MedalsGalleryWindow(self, self.current_achievements)

    def _setup_stats_panel(self):
        title = ctk.CTkLabel(
            self.stats_frame,
            text="ХАРАКТЕРИСТИКИ ПЕРСОНАЖА",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(padx=18, pady=(18, 12), anchor="w")

        for code in ["STR", "INT", "VIT", "FOC"]:
            card = ctk.CTkFrame(self.stats_frame, corner_radius=10)
            card.pack(fill="x", padx=18, pady=9)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=14, pady=(12, 2))

            lbl_name = ctk.CTkLabel(
                top_row,
                text=f"{code}",
                font=ctk.CTkFont(size=17, weight="bold"),
                text_color=STAT_COLORS.get(code, "#ffffff"),
            )
            lbl_name.pack(side="left")

            lbl_lvl = ctk.CTkLabel(
                top_row,
                text="Рівень 1",
                font=ctk.CTkFont(size=15, weight="bold"),
            )
            lbl_lvl.pack(side="right")

            lbl_desc = ctk.CTkLabel(
                card, text="", font=ctk.CTkFont(size=13), text_color="gray"
            )
            lbl_desc.pack(anchor="w", padx=14, pady=(0, 8))

            bar = ctk.CTkProgressBar(
                card, height=12, progress_color=STAT_COLORS.get(code, "#3498db")
            )
            bar.pack(fill="x", padx=14, pady=4)
            bar.set(0)

            lbl_xp = ctk.CTkLabel(card, text="0 / 100 XP", font=ctk.CTkFont(size=13))
            lbl_xp.pack(anchor="e", padx=14, pady=(2, 10))

            self.stat_widgets[code] = {
                "name": lbl_name,
                "level": lbl_lvl,
                "desc": lbl_desc,
                "bar": bar,
                "xp": lbl_xp,
            }

    def _setup_habits_tab(self):
        form = ctk.CTkFrame(self.tab_habits, corner_radius=8)
        form.pack(fill="x", padx=10, pady=10)

        self.entry_habit_title = ctk.CTkEntry(
            form,
            placeholder_text="Назва звички (напр. Силове тренування / 1 год Python)...",
            width=260,
            height=36,
        )
        self.entry_habit_title.pack(side="left", padx=8, pady=10, expand=True, fill="x")

        self.opt_habit_stat = ctk.CTkOptionMenu(
            form, values=["STR", "INT", "VIT", "FOC"], width=90, height=36
        )
        self.opt_habit_stat.pack(side="left", padx=4, pady=10)

        self.opt_habit_diff = ctk.CTkOptionMenu(
            form, values=["easy", "medium", "hard"], width=105, height=36
        )
        self.opt_habit_diff.set("medium")
        self.opt_habit_diff.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(
            form, text="+ Додати", width=105, height=36, command=self.add_habit_action
        ).pack(side="left", padx=8, pady=10)

        self.habits_scroll = ctk.CTkScrollableFrame(self.tab_habits, corner_radius=8)
        self.habits_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _setup_quests_tab(self):
        form = ctk.CTkFrame(self.tab_quests, corner_radius=8)
        form.pack(fill="x", padx=10, pady=10)

        self.entry_quest_title = ctk.CTkEntry(
            form, placeholder_text="Назва глобальної цілі (квесту)...", width=240, height=36
        )
        self.entry_quest_title.pack(side="left", padx=8, pady=10, expand=True, fill="x")

        self.opt_quest_stat = ctk.CTkOptionMenu(
            form, values=["STR", "INT", "VIT", "FOC"], width=90, height=36
        )
        self.opt_quest_stat.pack(side="left", padx=4, pady=10)

        self.entry_quest_xp = ctk.CTkEntry(form, placeholder_text="XP (150)", width=85, height=36)
        self.entry_quest_xp.insert(0, "150")
        self.entry_quest_xp.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(
            form, text="+ Квест", width=105, height=36, command=self.add_quest_action
        ).pack(side="left", padx=8, pady=10)

        self.quests_scroll = ctk.CTkScrollableFrame(self.tab_quests, corner_radius=8)
        self.quests_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _setup_logs_tab(self):
        self.logs_scroll = ctk.CTkScrollableFrame(self.tab_logs, corner_radius=8)
        self.logs_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_all(self):
        try:
            dash_resp = self.http.get(f"{self.api_url}/dashboard", timeout=10)
            habits_resp = self.http.get(f"{self.api_url}/habits", timeout=10)
            quests_resp = self.http.get(f"{self.api_url}/quests", timeout=10)
            dash_resp.raise_for_status()
            habits_resp.raise_for_status()
            quests_resp.raise_for_status()
        except requests.RequestException as e:
            messagebox.showerror("Помилка API", f"Не вдалося з'єднатися з FastAPI:\n{e}")
            return

        dashboard = dash_resp.json()
        habits = habits_resp.json()
        quests = quests_resp.json()

        self.current_hero_name = dashboard["name"]
        p_stat = dashboard.get("primary_stat", "STR")
        stat_color = STAT_COLORS.get(p_stat, "#e74c3c")

        # Оновлюємо великий портрет 125x125 та підсвічуємо рамку кольором класу
        sprite_file = dashboard.get("avatar_sprite", "str_m.png")
        header_sprite = load_pixel_sprite(sprite_file, self.HEADER_AVATAR_SIZE)
        if header_sprite:
            self.lbl_avatar.configure(image=header_sprite, text="")
        self.avatar_box.configure(border_color=stat_color)

        self.lbl_char_title.configure(
            text=f"{dashboard['name'].upper()}  |  РІВЕНЬ {dashboard['level']}"
        )
        self.lbl_char_perk.configure(
            text=f"Особливість: +20% до {p_stat} XP ({dashboard.get('gender', 'M')})",
            text_color=stat_color,
        )
        self.lbl_total_xp.configure(text=f"Загальний досвід: {dashboard['total_xp']} XP")
        self.lbl_hp.configure(text=f"HP: {dashboard['hp']} / {dashboard['max_hp']}")
        self.hp_bar.set(max(0.0, min(1.0, dashboard["hp"] / dashboard["max_hp"])))

        # Оновлюємо вітрину медалей та досягнень
        for child in self.medals_slots_box.winfo_children():
            child.destroy()

        achievements = dashboard.get("achievements", [])
        self.current_achievements = achievements
        current_codes = {a["code"] for a in achievements}

        if self.known_achievements is None:
            # Перше завантаження при запуску програми — запам'ятовуємо вже наявні медалі
            self.known_achievements = current_codes
        else:
            # Якщо під час роботи з'явилася нова медаль — показуємо вікно привітання!
            new_codes = current_codes - self.known_achievements
            self.known_achievements = current_codes
            for ach in achievements:
                if ach["code"] in new_codes:
                    self.after(200, lambda a=ach: MedalUnlockPopup(self, a))

        if not achievements:
            lbl_empty = ctk.CTkLabel(
                self.medals_slots_box,
                text="Поки немає відкритих трофеїв — натисніть сюди, щоб переглянути всі доступні медалі",
                font=ctk.CTkFont(size=13, slant="italic"),
                text_color="#555a66",
                cursor="hand2",
            )
            lbl_empty.pack(side="left", pady=4)
            lbl_empty.bind("<Button-1>", lambda e: self.open_medals_gallery())
        else:
            for ach in achievements:
                medal_img = load_medal_sprite(ach["sprite"], (54, 54))
                slot = ctk.CTkFrame(
                    self.medals_slots_box, fg_color="transparent", cursor="hand2"
                )
                slot.pack(side="left", padx=6, pady=2)
                slot.bind("<Button-1>", lambda e: self.open_medals_gallery())

                if medal_img:
                    lbl_m = ctk.CTkLabel(
                        slot, image=medal_img, text="", fg_color="transparent", cursor="hand2"
                    )
                    lbl_m.pack()
                    lbl_m.bind("<Button-1>", lambda e: self.open_medals_gallery())
                else:
                    lbl_m = ctk.CTkLabel(
                        slot, text="🏅", font=ctk.CTkFont(size=28), cursor="hand2"
                    )
                    lbl_m.pack()
                    lbl_m.bind("<Button-1>", lambda e: self.open_medals_gallery())

                lbl_t = ctk.CTkLabel(
                    slot,
                    text=ach["title"],
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#d4af37",
                    cursor="hand2",
                )
                lbl_t.pack()
                lbl_t.bind("<Button-1>", lambda e: self.open_medals_gallery())

        if not dashboard.get("is_registered", False) and not self.reg_window_opened:
            self.reg_window_opened = True
            self.after(150, lambda: RegistrationWindow(self, dashboard["name"]))

        for s in dashboard["stats"]:
            w = self.stat_widgets.get(s["code"])
            if w:
                bonus_tag = " ★ +20%" if s["code"] == p_stat else ""
                w["name"].configure(text=f"{s['code']} — {s['name']}{bonus_tag}")
                w["level"].configure(text=f"Рівень {s['level']}")
                w["desc"].configure(text=s["description"])
                xp_next = s["xp_to_next_level"]
                ratio = s["current_xp"] / xp_next if xp_next > 0 else 0
                w["bar"].set(max(0.0, min(1.0, ratio)))
                w["xp"].configure(text=f"{s['current_xp']} / {xp_next} XP")

        for child in self.habits_scroll.winfo_children():
            child.destroy()

        if not habits:
            ctk.CTkLabel(
                self.habits_scroll,
                text="Поки немає звичок. Додай першу вище!",
                text_color="gray",
            ).pack(pady=30)

        for h in habits:
            done_today = h["completed_today"]
            row = ctk.CTkFrame(self.habits_scroll, corner_radius=8)
            row.pack(fill="x", padx=4, pady=5)

            badge_color = STAT_COLORS.get(h["stat_code"], "#3498db")
            ctk.CTkLabel(
                row,
                text=f"[{h['stat_code']}]",
                font=ctk.CTkFont(weight="bold"),
                text_color=badge_color,
                width=50,
            ).pack(side="left", padx=(10, 4), pady=10)

            ctk.CTkLabel(
                row,
                text=f"{h['title']}  (+{h['base_xp']} XP | 🔥 Стрік: {h['streak']})",
                font=ctk.CTkFont(size=14),
            ).pack(side="left", padx=6, pady=10)

            ctk.CTkButton(
                row,
                text="✕",
                width=32,
                fg_color="#444444",
                hover_color="#c0392b",
                command=lambda hid=h["id"]: self.delete_habit_action(hid),
            ).pack(side="right", padx=(4, 10), pady=8)

            ctk.CTkButton(
                row,
                text="Виконано ✓" if done_today else "Виконати",
                width=110,
                fg_color="#27ae60" if not done_today else "#555555",
                state="disabled" if done_today else "normal",
                command=lambda hid=h["id"]: self.complete_habit_action(hid),
            ).pack(side="right", padx=4, pady=8)

        for child in self.quests_scroll.winfo_children():
            child.destroy()

        for q in quests:
            row = ctk.CTkFrame(self.quests_scroll, corner_radius=8)
            row.pack(fill="x", padx=4, pady=5)

            ctk.CTkLabel(
                row,
                text=f"[{q['stat_code']}] {q['title']} (+{q['xp_reward']} XP)",
                font=ctk.CTkFont(size=14, overstrike=q["is_completed"]),
            ).pack(side="left", padx=12, pady=10)

            if not q["is_completed"]:
                ctk.CTkButton(
                    row,
                    text="Завершити",
                    width=100,
                    fg_color="#8e44ad",
                    command=lambda qid=q["id"]: self.complete_quest_action(qid),
                ).pack(side="right", padx=10, pady=8)
            else:
                ctk.CTkLabel(row, text="Виконано ✓", text_color="#2ecc71").pack(
                    side="right", padx=15
                )

        for child in self.logs_scroll.winfo_children():
            child.destroy()

        for log in dashboard["recent_logs"]:
            row = ctk.CTkFrame(self.logs_scroll, corner_radius=6)
            row.pack(fill="x", padx=4, pady=3)

            xp_val = log["xp_change"]
            sign = f"+{xp_val}" if xp_val > 0 else f"{xp_val}"
            color = "#2ecc71" if xp_val > 0 else "#e74c3c"
            dt = datetime.fromisoformat(log["timestamp"])
            time_str = dt.strftime("%d.%m %H:%M")

            ctk.CTkLabel(
                row,
                text=f"{time_str} | [{log['stat_code']}] {log['title']}",
                font=ctk.CTkFont(size=13),
            ).pack(side="left", padx=10, pady=6)

            ctk.CTkLabel(
                row,
                text=f"{sign} XP",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color,
            ).pack(side="right", padx=12, pady=6)

    def add_habit_action(self):
        title = self.entry_habit_title.get().strip()
        if not title:
            return
        payload = {
            "title": title,
            "stat_code": self.opt_habit_stat.get(),
            "difficulty": self.opt_habit_diff.get(),
            "is_daily": True,
        }
        try:
            self.http.post(f"{self.api_url}/habits", json=payload, timeout=10)
            self.entry_habit_title.delete(0, "end")
            self.refresh_all()
        except requests.RequestException as e:
            messagebox.showerror("Помилка мережі", str(e))

    def complete_habit_action(self, habit_id: int):
        try:
            resp = self.http.post(
                f"{self.api_url}/habits/{habit_id}/complete", timeout=10
            )
            if resp.status_code != 200:
                detail = resp.json().get("detail", "Помилка виконання")
                messagebox.showwarning("Увага", detail)
            self.refresh_all()
        except requests.RequestException as e:
            messagebox.showerror("Помилка мережі", str(e))

    def delete_habit_action(self, habit_id: int):
        try:
            self.http.delete(f"{self.api_url}/habits/{habit_id}", timeout=10)
            self.refresh_all()
        except requests.RequestException as e:
            messagebox.showerror("Помилка мережі", str(e))

    def add_quest_action(self):
        title = self.entry_quest_title.get().strip()
        if not title:
            return
        try:
            xp = int(self.entry_quest_xp.get().strip())
        except ValueError:
            xp = 150
        payload = {
            "title": title,
            "stat_code": self.opt_quest_stat.get(),
            "xp_reward": xp,
        }
        try:
            self.http.post(f"{self.api_url}/quests", json=payload, timeout=10)
            self.entry_quest_title.delete(0, "end")
            self.refresh_all()
        except requests.RequestException as e:
            messagebox.showerror("Помилка мережі", str(e))

    def complete_quest_action(self, quest_id: int):
        try:
            resp = self.http.post(
                f"{self.api_url}/quests/{quest_id}/complete", timeout=10
            )
            if resp.status_code != 200:
                detail = resp.json().get("detail", "Помилка виконання")
                messagebox.showwarning("Увага", detail)
            self.refresh_all()
        except requests.RequestException as e:
            messagebox.showerror("Помилка мережі", str(e))