"""OfficeDadHouse_V2_Final -- build the whole scene into the geometry accumulator (house, rooms, lot, biome)."""
import odh_core as K
import odh_house as H
import odh_rooms as RM
import odh_site as ST
import odh_biome as BI


def build(biome=True):
    H.build_house()
    RM.rooms()
    ST.site()
    if biome:
        BI.biome()
    H.draw_door_leaves()
    H.room_lights()
