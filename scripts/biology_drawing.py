"""Bio A (生物科技館) / Bio B (生物教學大樓) drawing geometry.

Source: user-supplied floor plans buildings/bio-a/source/floor-{1,2,3}.pdf and
buildings/bio-b/source/floor-{1,2,3}.pdf (2026-11-23). Coordinates below are PDF
points read from the vector drawings (A 1F page, B 1F page); both pages are drawn
at about 9.40 pt per metre (A: 4357.5 cm = 409.92 pt, 2638.5 cm = 247.68 pt;
B: 4267.5 cm = 401.52 pt, 3709 cm = 348.96 pt).

Page orientation (both pages): page-right points from A to B (the model's
"-north" corridor axis), page-down points away from S01 towards S05 (model
"-east"). The connecting hall, flower plaza, sewage room and terraced
ramp/stairs share the vertical symmetry line x = AXIS_X on the A page; that line
is placed on the existing S05 T-stem joint, which stays fixed (user: the T deck
is the datum, its height follows S05).
"""
import math

A_SCALE = 409.92 / 43.575          # pt per metre on the A pages
B_SCALE = 401.52 / 42.675          # pt per metre on the B pages
AXIS_X = 467.4                     # common centre line of hall/plaza/terraces/sewage room (A page)
HALL_Y = (503.32 + 537.4) / 2      # hall centre line (A page)
HALL_A_END = 376.6                 # A service-wing glass end of the hall
HALL_B_END = 558.48                # B service-wing door frame
B_HALL_END_X = 107.3               # same B face on the B page
B_HALL_Y = (510.52 + 543.64) / 2   # hall centre on the B page

# Outer walls traced from the 1F vector drawings (window AC ledges, the A 1F
# north-end outside stair and small stair-tower jogs are left out).
A_RING = [(117.75, 204.3), (239.0, 204.3), (239.0, 376.5), (290.0, 376.5), (290.0, 500.5),
          (376.6, 500.5), (376.6, 575.0), (235.0, 575.0), (235.0, 629.5), (117.75, 629.5)]
B_RING = [(347.0, 210.0), (467.5, 210.0), (467.5, 636.5), (350.0, 636.5), (350.0, 583.0),
          (107.3, 583.0), (107.3, 507.0), (265.25, 507.0), (265.25, 383.0), (347.0, 383.0)]

# Connection (A page, pt).
HALL = (HALL_A_END, 503.32, HALL_B_END, 537.4)            # 1F glazed hall (outer faces)
HALL_RECESS = (436.3, 537.4, 498.2, 548.9)                 # hall floor reaching the sewage-room wall
DECK = (HALL_A_END, 497.4, HALL_B_END, 543.2)              # 2F open deck (dashed overhang lines)
PLAZA = (410.9, 372.52, 523.68, 503.32)                    # +510 flower plaza incl. threshold strip
PLAZA_SIDE = [(402.72, 380.68, 410.9, 493.5), (523.68, 380.68, 531.6, 493.5)]  # low planters
SEWAGE = (436.3, 548.9, 498.2, 596.2)                      # closed 污水機房 under the stem
SEWAGE_DOOR = (486.8, 496.8)                               # door leaf on its north wall (x range)
HALL_COLUMNS = [413.3, 438.5, 495.4, 521.3]                # square columns on both hall faces
PLAZA_DOORS = [(443.6, 461.6), (472.4, 491.1)]             # double doors hall -> plaza
SOUTH_DOORS = [(417.6, 433.5), (499.0, 517.0)]             # closed doors on the hall's S05 side
END_DOORS = {'a': (509.5, 524.0), 'b': (506.2, 524.2)}     # doors at both building ends

# Terraced ramp / stairs (+0 at S01 .. +500 at the plaza). x: walls 410.9/523.68,
# wall planter boxes to 417.4/517.0, side stair lanes 417.4-434.2 and 500.2-517.0,
# ramp field 434.2-500.2. y grows towards the plaza (uphill).
TERRACE = (410.9, 148.5, 523.68, 372.52)
LANES = {'left': (417.4, 434.2), 'right': (500.2, 517.0)}
FIELD = (434.2, 500.2)
WALL_BOX = [(410.9, 417.4), (517.0, 523.68)]
PERIOD = 60.48                     # one left+right cycle = 1.6 m rise (drawing)
RAMP_DY = 13.2                     # ramp centre-line run across the field (y)
RAMP_BAND = 13.8                   # ramp band height measured along y (≈1.44 m wide)
# Landing / stair stations (y) measured on the drawing, drawing heights in cm.
LEFT = [('landing', 148.5, 174.6, 0), ('stair', 174.6, 204.4, 0, 160, 10), ('landing', 204.4, 235.1, 160),
        ('stair', 235.1, 265.0, 160, 320, 10), ('landing', 265.0, 295.6, 320), ('stair', 295.6, 325.2, 320, 480, 10),
        ('landing', 325.2, 355.5, 480), ('stair', 355.5, 372.52, 480, 500, 2)]
RIGHT = [('landing', 148.5, 157.8, 0), ('stair', 157.8, 174.3, 0, 80, 5), ('landing', 174.3, 204.9, 80),
         ('stair', 204.9, 234.8, 80, 240, 10), ('landing', 234.8, 265.4, 240), ('stair', 265.4, 295.0, 240, 400, 10),
         ('landing', 295.0, 325.6, 400), ('stair', 325.6, 355.5, 400, 500, 6), ('landing', 355.5, 372.52, 500)]
# Ramps: centre line start (x,y) -> end (x,y), drawing heights. Ramp 7 ends on the +500 bay.
RAMPS = [((434.16, 167.8), (500.16, 181.0), 0, 80), ((500.16, 198.04), (434.16, 211.24), 80, 160),
         ((434.16, 228.28), (500.16, 241.48), 160, 240), ((500.16, 258.52), (434.16, 271.72), 240, 320),
         ((434.16, 288.76), (500.16, 301.96), 320, 400), ((500.16, 319.0), (434.16, 332.2), 400, 480),
         ((434.16, 349.24), (467.28, 355.72), 480, 500)]
TOP_BAY = (467.4, 355.5, 500.2, 372.52, 500)            # +500 bay where ramp 7 and the right stair arrive
TREE_PITS = [(496.0, 163.0), (438.4, 189.5), (496.0, 219.9), (438.4, 250.0), (496.0, 280.3), (438.4, 310.5),
             (496.0, 340.7), (438.4, 367.3)]   # 0.87 m square tree pits in the stepped planters
TREE_PIT_SIZE = 8.2
DRAWING_TOP = 510                 # plaza (+510) maps to the hall floor; +0 maps to S01


class Frame:
    """A-page points or B-page points -> world [x, z]."""
    def __init__(self, joint, north, east):
        self.joint, self.north, self.east = joint, north, east

    def local_a(self, x, y):
        return ((x - AXIS_X) / A_SCALE, (y - HALL_Y) / A_SCALE)

    def local_b(self, x, y):
        return ((HALL_B_END - AXIS_X) / A_SCALE + (x - B_HALL_END_X) / B_SCALE, (y - B_HALL_Y) / B_SCALE)

    def world(self, u, v):
        # page-right = -north, page-down = -east
        return [round(self.joint[i] - self.north[i] * u - self.east[i] * v, 7) for i in range(2)]

    def a(self, x, y):
        return self.world(*self.local_a(x, y))

    def b(self, x, y):
        return self.world(*self.local_b(x, y))

    def rect(self, r):
        x0, y0, x1, y1 = r
        return [self.a(x0, y0), self.a(x1, y0), self.a(x1, y1), self.a(x0, y1)]


def ccw(ring):
    area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(ring, ring[1:] + ring[:1]))
    return ring if area > 0 else ring[::-1]
