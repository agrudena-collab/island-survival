"""review PDF: python build_pdf.py FRAMES_DIR OUT.pdf  (reportlab, DejaVu for Cyrillic)"""
import sys, os
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
cv.setTitle('Office Dad House V2 — на проверку')
M = 28


def img(name, x, y, w, h):
    p = os.path.join(fd, name + '.png')
    im = Image.open(p)
    ar = im.width / im.height
    iw, ih = (w, w / ar) if w / h < ar else (h * ar, h)
    import io
    bio = io.BytesIO(); im.convert('RGB').save(bio, 'JPEG', quality=88); bio.seek(0)
    cv.drawImage(ImageReader(bio), x + (w - iw) / 2, y + (h - ih) / 2, iw, ih)
    return iw, ih


def head(t, sub=None):
    cv.setFont('DJB', 18)
    cv.drawString(M, H - 38, t)
    if sub:
        cv.setFont('DJ', 9.5)
        cv.drawString(M, H - 54, sub)


def cap(t, x, y):
    cv.setFont('DJ', 8.5)
    cv.drawString(x, y, t)


def page():
    cv.showPage()


def text(lines, x, y, size=10, lead=14, font='DJ'):
    cv.setFont(font, size)
    for l in lines:
        cv.drawString(x, y, l)
        y -= lead
    return y


# 1 title
cv.setFont('DJB', 28)
cv.drawString(M, H - 80, 'Office Dad House V2 — дом 2 из 8')
cv.setFont('DJ', 12)
cv.drawString(M, H - 102, 'Материал на проверку: дом, участок и биом вокруг (Blender, этап до Studio)')
img('01_street_front', M, 60, W - 2 * M, H - 150)
page()

# 2 spec
head('Что в доме', 'проверено в Blender · Studio-этап ещё не сделан')
y = H - 84
y = text([
    '• 2 этажа, корпус 54×67 + пристройка гаража, участок 104×100 (не меньше Regular Dad V2).',
    '• 1 этаж: прихожая → гостиная → столовая → кухня → прихожая (кольцо), лестница, холл, WC, библиотека,',
    '  прачечная с задней дверью, гараж.',
    '• 2 этаж: кабинет отца с балконом (отец с портфелем у окна), спальня родителей, детская, ванная, лаунж, гостевая.',
    '• Укрытия: кладовка в прачечной (1 эт.), шкаф-ниша в спальне родителей (2 эт.), ниша за глухим книжным шкафом (2 эт.).',
    '• LowCover: диван, остров кухни, кровати, кресла, сундук (высота 2.6–3.6). Стеклянный стол — не укрытие.',
    '• Участок: забор, FamilyLotBounds, CaughtSpawn, сарай, задний двор под балконом, детская площадка, сад.',
], M, y)
y -= 8
y = text(['Способы проникновения'], M, y, 12, 16, 'DJB')
y = text([
    '1. Рабочий пропуск Office Dad, забытый в машине на подъездной дорожке → открывает служебную дверь гаража.',
    '2. Лестница из города → задний двор под балконом → балкон → кабинет.',
    'Выходы (парадная/задняя дверь, калитки) открываются изнутри без ключа. Семья: жена, сын, собака.',
], M, y)
y -= 8
y = text(['Проверено'], M, y, 12, 16, 'DJB')
y = text([
    '• Аудит: 0 проблем (пересечения мебели, «парящая» мебель, шторы у окон, зона открытия дверей).',
    '• Проходимость: все комнаты обоих этажей достижимы; двери ≥5.6; лестница 6.25 шириной, 15 ступеней.',
    '• Экспорт: дом 145 MeshPart, биом 270 (с машиной), максимум 9000 треугольников на меш, цвет вершин, без текстур, без швов и наложений (аудит территории: 0).',
], M, y)
y -= 8
y = text(['НЕ проверено / требует решения'], M, y, 12, 16, 'DJB')
y = text([
    '• Roblox Studio: импорт FBX, скрипты apply_*.luau, теги, Pathfinding, углы дверей, модель .rbxm (нет).',
    '• Нужна правка src (я не менял): подсказка «Запасной ключ взят» → «Пропуск взят»; роль Dog в FamilyNpcService.',
    '• Соседние дома биома — сгенерированные пустые офисные, а не FBX GrillDad/Lakeside/RegularDad.',
], M, y)
page()

# 3,4 plans
head('План 1 этажа', 'вид сверху без кровли и 2 этажа')
img('30_plan_ground', M, 30, W - 2 * M, H - 90)
page()
head('План 2 этажа', 'вид сверху без кровли')
img('31_plan_upper', M, 30, W - 2 * M, H - 90)
page()

# exterior
head('Участок и дом')
hw = (W - 3 * M) / 2
img('02_back_yard_ladder', M, 120, hw, H - 190)
img('03_driveway_car_pass', M * 2 + hw, 120, hw, H - 190)
cap('Задний двор под балконом (место лестницы), сарай, патио', M, 100)
cap('Подъездная дорожка: машина с пропуском Office Dad', M * 2 + hw, 100)
page()
head('Биом вокруг', 'улица, пустые офисные дома с участками, банк, супермаркет')
img('04_biome_overview', M, 120, hw, H - 190)
img('05_supermarket_bank', M * 2 + hw, 120, hw, H - 190)
cap('Вид сверху', M, 100)
cap('Супермаркет и банк', M * 2 + hw, 100)
page()

# interiors, 2 per page
pairs = [('10_foyer', '12_living', 'Прихожая', 'Гостиная'), ('13_kitchen', '14_dining', 'Кухня', 'Столовая'),
         ('15_library', '16_utility_cupboard', 'Библиотека', 'Прачечная и кладовка-укрытие'), ('11_hall_stairs', '17_garage', 'Холл и лестница', 'Гараж'),
         ('20_master', '21_master_wardrobe', 'Спальня родителей', 'Шкаф-укрытие'), ('22_kid', '23_bath', 'Детская', 'Ванная'),
         ('24_lounge_niche', '25_guest', 'Лаунж и ниша за шкафом', 'Гостевая'), ('26_office_father', '27_upper_hall', 'Кабинет отца', 'Холл 2 этажа')]
for a, b, ta, tb in pairs:
    head('Интерьер')
    img(a, M, 90, hw, H - 160)
    img(b, M * 2 + hw, 90, hw, H - 160)
    cap(ta, M, 70)
    cap(tb, M * 2 + hw, 70)
    page()
cv.save()
print('pdf ok')
