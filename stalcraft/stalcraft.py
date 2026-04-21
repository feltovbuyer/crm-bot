from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# --- ПЕРЕМЕННЫЕ ИГРЫ ---
resources = {"зуб_собаки": 0, "аптечка": 1}
hp = 100

# --- ОКРУЖЕНИЕ ---
Sky(color=color.black90)
ground = Entity(model='plane', collider='box', scale=100, texture='grass', color=color.rgb(60, 70, 60))
scene.fog_density = 0.04

# --- ЗВУКИ (Загрузка) ---
# Если файлов нет, Ursina просто выдаст предупреждение, но не вылетит
shoot_sound = Audio('assets/shot.mp3', loop=False, autoplay=False)
ambient_music = Audio('assets/ambient.mp3', loop=True, autoplay=True)

# --- ИНТЕРФЕЙС ---
info_text = Text(text=f"Зубы: {resources['зуб_собаки']} | HP: {hp}", position=(-0.85, 0.45), scale=1.5)


# --- МОБ (Мутант) ---
class Mutant(Entity):
    def __init__(self, position=(10, 1, 10)):
        super().__init__(
            model='cube', color=color.red, collider='box',
            position=position, scale=(1, 2, 1)
        )
        self.health = 3

    def update(self):
        # Идет к игроку
        direction = player.position - self.position
        self.position += direction.normalized() * time.dt * 2

        # Если подошел вплотную - бьет
        if distance(self.position, player.position) < 1.5:
            global hp
            hp -= 10 * time.dt
            info_text.text = f"Зубы: {resources['зуб_собаки']} | HP: {round(hp)}"


# Создаем одного мутанта для теста
enemy = Mutant(position=(15, 1, 15))

# --- ОРУЖИЕ И СТРЕЛЬБА ---
gun = Entity(parent=camera, model='cube', scale=(0.1, 0.1, 1), position=(0.5, -0.5, 1), color=color.black)


def shoot():
    shoot_sound.play()
    # Проверка попадания
    if mouse.hovered_entity and isinstance(mouse.hovered_entity, Mutant):
        mouse.hovered_entity.health -= 1
        if mouse.hovered_entity.health <= 0:
            destroy(mouse.hovered_entity)
            resources["зуб_собаки"] += 1
            info_text.text = f"Зубы: {resources['зуб_собаки']} | HP: {round(hp)}"


# --- БАРМЕН И БАРТЕР ---
bartender = Entity(model='cube', collider='box', position=(0, 1, 5), color=color.orange)


def input(key):
    if key == 'left mouse down':
        shoot()

    if key == 'f' and distance(player, bartender) < 4:
        # Логика бартера: 5 зубов = новая пушка (визуально меняем цвет)
        if resources["зуб_собаки"] >= 5:
            resources["зуб_собаки"] -= 5
            gun.color = color.gold  # Типа "Золотой ствол"
            print("Бармен: Держи обновку!")
        else:
            print(f"Бармен: Мало хабара! Нужно еще {5 - resources['зуб_собаки']} зубов.")


player = FirstPersonController()

app.run()