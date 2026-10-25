"""car reference sheet: python3 build_car_pdf.py FRAMES_DIR OUT.pdf"""
import sys, os, io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image

fd, out = sys.argv[1], sys.argv[2]
pdfmetrics.registerFont(TTFont('DJ', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DJB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
W, H = landscape(A4)
cv = canvas.Canvas(out, pagesize=(W, H))
cv.setTitle('Машина Office Dad — модель и референсы')
M = 28


def img(name, x, y, w, h):
    im = Image.open(os.path.join(fd, name + '.png'))
    ar = im.width / im.height
    iw, ih = (w, w / ar) if w / h < ar else (h * ar, h)
    bio = io.BytesIO(); im.convert('RGB').save(bio, 'JPEG', quality=88); bio.seek(0)
    cv.drawImage(ImageReader(bio), x + (w - iw) / 2, y + (h - ih) / 2, iw, ih)


def head(t, sub=None):
    cv.setFont('DJB', 18); cv.drawString(M, H - 38, t)
    if sub:
        cv.setFont('DJ', 9.5); cv.drawString(M, H - 54, sub)


def cap(t, x, y):
    cv.setFont('DJ', 8.5); cv.drawString(x, y, t)


def lines(items, x, y, size=10, lead=15):
    cv.setFont('DJ', size)
    for t in items:
        cv.drawString(x, y, t); y -= lead


head('Машина Office Dad: отдельная модель', 'Седан среднего класса, тёмно-синий. Входит в export/OfficeDadBiome_V2.fbx (вершинные цвета, без текстур, без швов)')
img('car_front34', M, 60, W / 2 - M - 10, H - 130)
img('car_rear34', W / 2 + 10, H / 2 - 20, W / 2 - M - 10, H / 2 - 60)
img('car_inside', W / 2 + 10, 60, W / 2 - M - 10, H / 2 - 70)
cap('Спереди и сзади (рендер Blender)', M, 40)
cv.showPage()

head('Чертёж (ортографические виды)', 'Модель в игровом масштабе (0.78 от полного размера): 1 stud ≈ 0.39 м. Все виды из одной модели.')
img('bp_side', M, H / 2 - 20, W / 2 - M - 10, H / 2 - 70); cap('Сбоку', M, H / 2 - 30)
img('bp_top', W / 2 + 10, H / 2 - 40, W / 2 - M - 10, H / 2 - 50); cap('Сверху', W / 2 + 10, H / 2 - 50)
img('bp_front', M, 40, W / 2 - M - 10, H / 2 - 80); cap('Спереди', M, 28)
img('bp_rear', W / 2 + 10, 40, W / 2 - M - 10, H / 2 - 100); cap('Сзади', W / 2 + 10, 28)
cv.showPage()

head('Референсы и размеры', 'Опорный класс: среднеразмерный седан (класс Camry / Accord / Mazda6)')
lines([
    'Параметр                      Реальный класс (м)       Модель (stud / м при 0.3 м)',
    'Длина                         4.8 – 4.9                11.9 stud ≈ 4.6 м (чуть короче для лота)',
    'Ширина (без зеркал)           1.84 – 1.86              4.9 stud ≈ 1.9 м',
    'Высота                        1.44 – 1.46              3.7 stud ≈ 1.45 м',
    'Колёсная база                 2.78 – 2.83              7.2 stud ≈ 2.8 м',
    'Диаметр колеса                0.64 – 0.68              2.0 stud ≈ 0.78 м (чуть крупнее для читаемости)',
], M, H - 90, 9.5, 16)
lines([
    'Что в модели: гладкий лофт-кузов (скруглённые сечения), стекло, крыша, стойки, зеркала, ручки дверей,',
    'решётка, фары, противотуманки, задние фонари, бамперы, номера, выхлоп, антенна, колёса (шина, диск,',
    'спицы, ступица), арки, днище. Полная отделка салона: ковёр, потолок, карточки дверей с подлокотниками,',
    'панель с приборами, экраном и дефлекторами, бардачок, руль, педали, консоль с рычагом, сиденья, ремни.',
    'Руль слева. Пропуск лежит на панели: геометрия',
    'пропуска и деталь SpareKey строятся в Studio по якорю work_pass (в FBX машины пропуска нет).',
    '',
    'Честно о референсах: фото-референсы в чертёж не вставлены. Из облака я не скачиваю чужие фото;',
    'пропорции и размеры взяты из открытых технических характеристик класса. Если пришлёшь фото',
    'конкретной машины (любые ракурсы), подгоню силуэт, фары и колёса под неё.',
    '',
    'Ориентация: нос машины в сторону +z локальной системы (как у остальных моделей), начало координат',
    'в центре машины на земле. На участке стоит носом к улице; в FBX участка машины нет, ставится отдельно.',
], M, H - 215, 10, 15)
cv.showPage()
cv.save()
print('pdf ok')
