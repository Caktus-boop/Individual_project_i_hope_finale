from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

buttons = [
    [KeyboardButton(text="Столовая"), KeyboardButton(text="ВХОД"), KeyboardButton(text="Спортзал")],
    [KeyboardButton(text="Левое крыло(2)"), KeyboardButton(text="Рекреация(2)"), KeyboardButton(text="Правое крыло(2)")],
    [KeyboardButton(text="Левое крыло(3)"), KeyboardButton(text="Рекреация(3)"), KeyboardButton(text="Правое крыло(3)")],
    [KeyboardButton(text="Левое крыло(4)"), KeyboardButton(text="Рекреация(4)"), KeyboardButton(text="Правое крыло(4)")],
]

main = ReplyKeyboardMarkup(
    keyboard=buttons,
    resize_keyboard=True
)