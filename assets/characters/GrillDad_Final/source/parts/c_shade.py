

def sh_const(name):
    return lambda n, c: name


def sh_skin(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    return "SKIN"


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    if n.y < -0.62:
        return "SKIN_LIGHT"
    return "SKIN"


def sh_shirt(n, c):
    if n.z > 0.45:
        return "SHIRT_LIGHT"
    if abs(n.x) > 0.75 or n.z < -0.45:
        return "SHIRT_DARK"
    return "SHIRT"


def sh_pants(n, c):
    if n.z < -0.6 or abs(n.x) > 0.85:
        return "PANTS_DARK"
    if n.z > 0.6 or n.y < -0.62:
        return "PANTS_LIGHT"
    return "PANTS"


def sh_shoe(n, c):
    if n.z < -0.5:
        return "SOLE"
    if n.z > 0.55 or abs(n.x) > 0.8:
        return "SHOE_LIGHT"
    return "SHOE"


def sh_hair(n, c):
    if n.z < -0.30:
        return "HAIR_DARK"
    if n.z > 0.62:
        return "HAIR_LIGHT"
    return "HAIR"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SKIN_SHADOW"
    if n.z > 0.45:
        return "SKIN_LIGHT"
    return "NOSE"


def sh_apron(n, c):
    if n.y < -0.6:
        # sparse large lighter facets on the front face, chosen deterministically from the face centre
        k = (int(math.floor(c.x * 2.6)) * 7 + int(math.floor(c.z * 2.6)) * 13) % 11
        return "APRON_LIGHT" if k == 0 else "APRON"
    return "APRON_DARK"


def sh_wood(n, c):
    if n.z < -0.5:
        return "WOOD_DARK"
    if n.x * (1 if c.x >= 0 else -1) > 0.55:
        return "WOOD_LIGHT"
    if n.x * (1 if c.x >= 0 else -1) < -0.55:
        return "WOOD_DARK"
    return "WOOD"


def sh_steel(n, c):
    if n.z > 0.7:
        return "STEEL_LIGHT"
    if abs(n.x) > 0.75:
        return "STEEL_DARK"
    if n.y > 0.5:
        return "STEEL_DARK"
    return "STEEL"
