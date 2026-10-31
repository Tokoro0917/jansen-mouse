"""機体（脚以外）の配置と検証: 部品の干渉、壁センサの見通し、旋回半径、重量・重心。

座標系（機体）: x = 前方、y = 左、z = 上（床が 0）。クランク軸は x = 0, z = クランク高さ。
脚モジュールは左右の |y| = CENTER_WIDTH/2 より外側にあり、クランク 1 回転で掃引する範囲は
xz 平面の多角形 × モジュールの y 範囲で表す。部品は直方体で表す。

脚が占めない場所は「中央の溝（|y| < CENTER_WIDTH/2）」「最も外側のフレーム板の外」「脚より上」だけで、
部品と壁センサはそこに置く必要がある。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import LineString, MultiPoint, Point, box
from shapely.ops import unary_union

from .assembly import BuildParams, _module_poses, _shape, module_parts, solve_layers
from .linkage import JansenLeg, gait_metrics

WALL_HALF_GAP = 84.0     # 区画中心から壁面まで（180/2 - 6）[mm]
WALL_HEIGHT = 50.0       # 迷路の壁の高さ [mm]
FR4_DENSITY = 1.85e-3    # [g/mm^3]
BEAM_HALF_ANGLE = 10.0   # 壁センサの光の広がり（円すいの半角）[deg]。KOGUMA Mk4 と同じく円すいで遮りを調べる

# 壁センサのホルダ（KOGUMA Mk4 / ToraNeko.Mk3 と同じ形。黒い樹脂で発光の光が受光に直接入らないようにする）
# 基板の裏（下）にさかさまに付け、発光 OPV332 を基板から遠い穴、受光 SFH 229 FA を近い穴に入れる。
HOLDER_W, HOLDER_D, HOLDER_H = 6.0, 4.04, 9.9    # 幅（光と直角）、奥行き（光の向き）、高さ [mm]
HOLDER_EMITTER_DEPTH = 7.6                       # 基板の下面から発光の穴の中心まで [mm]
HOLDER_RECEIVER_DEPTH = 3.2                      # 基板の下面から受光の穴の中心まで [mm]
STEEL_DENSITY = 7.85e-3


@dataclass
class Component:
    """直方体の部品。mount はその部品が取り付く相手（干渉判定から除く）。"""

    name: str
    x: tuple[float, float]
    y: tuple[float, float]
    z: tuple[float, float]
    mass_g: float
    color: str = "SlateGray"
    note: str = ""

    def center(self):
        return tuple(sum(r) / 2 for r in (self.x, self.y, self.z))


@dataclass
class Sensor:
    name: str
    origin: tuple[float, float, float]   # 発光・受光部の位置
    direction_deg: float                 # xy 平面での向き（前 = 0, 左 = +90）
    board: str                           # 取り付く基板（見通し判定から除く）


@dataclass
class Obstacle:
    """y 範囲 [y0, y1] に、xz 平面の多角形 poly で表される脚・フレームの占有域。"""

    name: str
    y0: float
    y1: float
    poly: object


@dataclass
class BodyDesign:
    scale: float
    throws: int
    center_width: float
    build: BuildParams
    components: list[Component] = field(default_factory=list)
    sensors: list[Sensor] = field(default_factory=list)


# ---------------------------------------------------------------- 脚・フレームの占有域
def leg_obstacles(scale: float, throws: int, center_width: float, bp: BuildParams) -> tuple[list[Obstacle], float]:
    leg = JansenLeg(scale=scale)
    h = -gait_metrics(leg).ground_y
    layout = solve_layers(leg, bp)
    parts = module_parts()
    sweep = unary_union([
        _shape(n, js, _module_poses(leg, 2 * math.pi * s / bp.samples), leg, bp)
        for s in range(bp.samples) for n, js in parts.items()])
    web = Point(0, 0).buffer(leg.length("m") + bp.link_width / 2 + 1.0)
    module_xy = unary_union([sweep, web])
    r = bp.link_width / 2
    la, ll = leg.length("a"), leg.length("l")
    frame = MultiPoint([(-la, -ll), (la, -ll), (0, 0), (-la, bp.spacer_y), (la, bp.spacer_y)]).convex_hull.buffer(r + 1)

    def to_xz(poly):  # 脚座標 (x, y_rel) -> 機体 (x, z)
        from shapely import affinity
        return affinity.translate(poly, 0, h)

    pitch = bp.plate + bp.washer
    obs = []
    for side in (1, -1):
        y = center_width / 2
        for m in range(throws):
            obs.append(Obstacle(f"frame{m}{'L' if side > 0 else 'R'}", *sorted((side * y, side * (y + bp.plate))), to_xz(frame)))
            y += bp.plate
            t = (layout.n_layers + 2) * pitch
            obs.append(Obstacle(f"legs{m}{'L' if side > 0 else 'R'}", *sorted((side * y, side * (y + t))), to_xz(module_xy)))
            y += t
        obs.append(Obstacle(f"frame{throws}{'L' if side > 0 else 'R'}", *sorted((side * y, side * (y + bp.plate))), to_xz(frame)))
    return obs, h


# ---------------------------------------------------------------- 標準の配置
def default_design(scale: float, throws: int, center_width: float, bp: BuildParams) -> BodyDesign:
    """標準の部品配置。寸法・重量は代表的な市販品の値で、購入品に合わせて直す（docs/hardware.md）。"""
    obs, h = leg_obstacles(scale, throws, center_width, bp)
    outer = max(abs(o.y1) for o in obs)  # 最も外側のフレーム板の外面
    frame_top = max(o.poly.bounds[3] for o in obs if o.name.startswith("frame"))
    deck_z = frame_top + 2.0
    cw = center_width / 2
    la = JansenLeg(scale=scale).length("a")
    motor_x = (-34.0, 7.0)
    clamp_x = (motor_x[0] - 4, motor_x[1] + 4)       # モータ押さえのネジ（モータの前後の端の外）
    bridge_x = (clamp_x[0] - 3, max(clamp_x[1], la) + 3)
    bridge_z = (h + 7.5, deck_z)
    bw = center_width - 1
    bh = bridge_z[1] - bridge_z[0]
    # ブリッジの体積: 天板 2.5 mm + タイロッドの所のリブ 5 mm × 2 + モータ押さえのボス φ6 × 2（樹脂は 6 割）
    bridge_vol = ((bridge_x[1] - bridge_x[0]) * bw * 2.5 + 2 * 5.0 * bw * bh + 2 * math.pi * 3.0 ** 2 * bh)
    d = BodyDesign(scale, throws, center_width, bp)
    d.components = [
        # 中央の溝にモータ 2 個を横に並べる。出力軸（直交）がクランク軸と同軸で、内側のフレーム板を貫いて
        # 最初のクランクウェブに直接入る。本体は後ろ向きに伸ばし、前方は前壁センサのために空ける。
        Component("motor_L", motor_x, (0.5, cw - 0.5), (h - 7, h + 7), 12.0, "Silver",
                  "N20 ウォームギヤモータ + エンコーダ（外形 12 x 14 x 41 を仮定）"),
        Component("motor_R", motor_x, (-(cw - 0.5), -0.5), (h - 7, h + 7), 12.0, "Silver",
                  "同上"),
        # メイン基板は脚とフレーム板より上。機体の幅いっぱいまで使える。前に細い舌を出し、壁センサ基板を吊る
        Component("deck", (-40, 40), (-30, 30), (deck_z, deck_z + 1.0), 80 * 60 * 1.0 * FR4_DENSITY, "DarkGreen",
                  "メイン基板 80 x 60 x t1.0（ブリッジの上面にネジ止め）"),
        Component("deck_front", (40, SENSOR_BOARD_X1), (-(cw - 0.5), cw - 0.5), (deck_z, deck_z + 1.0),
                  (SENSOR_BOARD_X1 - 40) * bw * 1.0 * FR4_DENSITY, "DarkGreen",
                  "メイン基板の前の舌（下に壁センサ基板を吊る）"),
        Component("mcu", (-26, 27), (-10.5, 10.5), (deck_z + 1, deck_z + 5), 4.5, "Navy", "Black Pill（ピンヘッダなし、直付け）"),
        Component("battery", (-20, 14), (13, 31), (deck_z + 1, deck_z + 13), 13.0, "Gold", "2S LiPo 200 mAh"),
        Component("imu", (-6, 6), (-28, -16), (deck_z + 1, deck_z + 2), 1.0, "Purple", "ICM-20602 基板"),
        Component("driver", (28, 38), (-28, -16), (deck_z + 1, deck_z + 3), 1.0, "Maroon", "DRV8835 基板"),
        # ブリッジ（3D プリント、旧「中央シャーシ」）: 左右の内側フレーム板をタイロッドでつなぎ、
        # モータを上から押さえ、上面にメイン基板を付ける。必要な所（天板・リブ・ボス）だけの形。
        Component("bridge", bridge_x, (-(cw - 0.5), cw - 0.5), bridge_z, bridge_vol * 0.6 * 1.24e-3,
                  "LightSteelBlue", "ブリッジ（PLA）。天板とタイロッドの所のリブだけ"),
        # 壁センサ基板（KOGUMA Mk4 と同じく 4 本を 1 枚に）: 水平に置き、ホルダを裏に下げる。
        # メイン基板の舌から M2 スペーサ 4 本で吊る（スペーサは光の円すいを避けた位置）
        Component("sensor_board", (40, SENSOR_BOARD_X1), (-(cw - 0.5), cw - 0.5), (SENSOR_BOARD_Z, SENSOR_BOARD_Z + 0.8),
                  (SENSOR_BOARD_X1 - 40) * bw * 0.8 * FR4_DENSITY + 1.0, "Teal",
                  "壁センサ基板 t0.8（発光の定電流ドライバ・受光アンプを含む）"),
    ]
    for i, (sx, sy) in enumerate(SENSOR_STANDOFFS):
        d.components.append(Component(f"standoff{i}", (sx - 2, sx + 2), (sy - 2, sy + 2),
                                      (SENSOR_BOARD_Z + 0.8, deck_z), 0.3, "Gray", "M2 スペーサ（樹脂）"))
    for name, (x, y), a in SENSOR_LAYOUT:
        d.components.append(holder_component(name, x, y, a))
    d.sensors = [Sensor(name, (x, y, beam_z()), a, f"holder_{name}") for name, (x, y), a in SENSOR_LAYOUT]
    return d


# 壁センサの配置（ホルダの前の面の真ん中、光の向き [deg]: 前 = 0, 左 = +90）
# - FL / FR: 中央の溝の中で真正面。前の壁まで 34 mm。左右の差で前の壁に対する傾きを見る
# - L / R: 脚より前（x 60）で真横。脚はセンサの高さでは |x| 44 mm までしか来ないので、光の円すいが脚に当たらない
# KOGUMA Mk4 は前を外へ 7°、横を交差させて前の柱を見るが、本機は区画中心で止まってその区画の壁を見るので、
# 前は平行（傾きの検出のため）、横は真横（その区画の横壁、柱から 24 mm 離れた所を見る）にした。
SENSOR_BOARD_X1 = 64.0   # センサ基板・メイン基板の舌の前端 [mm]
# 壁センサ基板を吊るスペーサの位置 (x, y)。ホルダと光の円すいを避ける（sensor_blockers で確認）
SENSOR_STANDOFFS = [(42.0, 9.0), (42.0, -9.0), (53.0, 10.5), (53.0, -10.5)]
SENSOR_BOARD_Z = 45.0    # センサ基板の下面の高さ [mm]
SENSOR_LAYOUT = [
    ("FL", (50.0, 5.0), 0.0),
    ("FR", (50.0, -5.0), 0.0),
    ("L", (60.0, 13.0), 90.0),
    ("R", (60.0, -13.0), -90.0),
]


def beam_z() -> float:
    """光の高さ: 発光と受光の穴の中間。"""
    return SENSOR_BOARD_Z - (HOLDER_EMITTER_DEPTH + HOLDER_RECEIVER_DEPTH) / 2


def holder_component(name: str, x: float, y: float, a_deg: float) -> Component:
    """ホルダの外形（前の面の真ん中 (x, y)、光の向き a）を直方体で表す。向きは 0 / ±90° のみ。"""
    hw, d = HOLDER_W / 2, HOLDER_D
    if abs(a_deg) < 1e-6:
        xs, ys = (x - d, x), (y - hw, y + hw)
    elif abs(a_deg - 90) < 1e-6:
        xs, ys = (x - hw, x + hw), (y - d, y)
    elif abs(a_deg + 90) < 1e-6:
        xs, ys = (x - hw, x + hw), (y, y + d)
    else:
        raise ValueError("ホルダの向きは 0 / ±90° のみ")
    return Component(f"holder_{name}", xs, ys, (SENSOR_BOARD_Z - HOLDER_H, SENSOR_BOARD_Z), 0.22, "Black",
                     "壁センサのホルダ（黒い樹脂）+ OPV332 + SFH 229 FA")


def legacy_sensors() -> list[Sensor]:
    """以前の配置（脚の掃引域を考えていなかった）。検証で不可能なことを示すために残す。"""
    return [
        Sensor("FL(旧)", (45.0, 20.0, 30.0), 0.0, ""),
        Sensor("FR(旧)", (45.0, -20.0, 30.0), 0.0, ""),
        Sensor("L(旧)", (35.0, 15.0, 30.0), 90.0, ""),
        Sensor("R(旧)", (35.0, -15.0, 30.0), -90.0, ""),
    ]


# ---------------------------------------------------------------- 検証
def _xz(c: Component):
    return box(c.x[0], c.z[0], c.x[1], c.z[1])


def _overlap(a0, a1, b0, b1, margin=0.0):
    return a0 < b1 - margin and b0 < a1 - margin


def component_interference(d: BodyDesign, obs: list[Obstacle], clearance: float = 0.5) -> list[str]:
    problems = []
    for c in d.components:
        for o in obs:
            if _overlap(c.y[0], c.y[1], o.y0, o.y1) and _xz(c).distance(o.poly) < clearance:
                problems.append(f"{c.name} が {o.name} と干渉")
    for i, a in enumerate(d.components):
        for b in d.components[i + 1:]:
            if (_overlap(a.x[0], a.x[1], b.x[0], b.x[1]) and _overlap(a.y[0], a.y[1], b.y[0], b.y[1])
                    and _overlap(a.z[0], a.z[1], b.z[0], b.z[1])):
                problems.append(f"{a.name} と {b.name} が重なる")
    return problems


def sensor_ray(s: Sensor) -> tuple[tuple[float, float], tuple[float, float]]:
    """センサから、区画中心にいるときの壁面（前壁 x = 84 / 横壁 |y| = 84）までの xy 線分。"""
    ox, oy, _ = s.origin
    a = math.radians(s.direction_deg)
    dx, dy = math.cos(a), math.sin(a)
    t = (WALL_HALF_GAP - (ox if abs(dx) > abs(dy) else abs(oy))) / max(abs(dx), abs(dy))
    return (ox, oy), (ox + dx * t, oy + dy * t)


def sensor_blockers(d: BodyDesign, obs: list[Obstacle], sensors: list[Sensor] | None = None,
                    half_angle_deg: float = BEAM_HALF_ANGLE) -> dict[str, list[str]]:
    """各センサの光（半角 half_angle_deg の円すい）を遮るもの。円すいの中心・上下・左右の 5 本の線で調べる。"""
    out = {}
    t_half = math.tan(math.radians(half_angle_deg))
    for s in sensors if sensors is not None else d.sensors:
        (x0, y0), (x1, y1) = sensor_ray(s)
        length = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        nx, ny = -uy, ux  # 水平で光と直角
        z0 = s.origin[2]
        blockers = []
        n = 120
        for i in range(1, n + 1):
            dist = length * i / n
            spread = 1.0 + dist * t_half  # 発光部の大きさ（φ3）+ 広がり
            for off_h, off_v in ((0, 0), (spread, 0), (-spread, 0), (0, spread), (0, -spread)):
                px = x0 + ux * dist + nx * off_h
                py = y0 + uy * dist + ny * off_h
                pz = z0 + off_v
                for o in obs:
                    if o.name not in blockers and o.y0 <= py <= o.y1 and o.poly.contains(Point(px, pz)):
                        blockers.append(o.name)
                for c in d.components:
                    if c.name == s.board or c.name in blockers:
                        continue
                    if c.x[0] <= px <= c.x[1] and c.y[0] <= py <= c.y[1] and c.z[0] <= pz <= c.z[1]:
                        blockers.append(c.name)
        if z0 > WALL_HEIGHT - 5:
            blockers.append(f"高さ {z0:.0f} mm が壁（{WALL_HEIGHT:.0f} mm）に近すぎる")
        out[s.name] = blockers
    return out


def turning_radius(d: BodyDesign, obs: list[Obstacle]) -> tuple[float, str]:
    """超信地旋回で掃引する円の半径（機体中心から最も遠い点）。"""
    best, who = 0.0, ""
    for o in obs:
        xmax = max(abs(o.poly.bounds[0]), abs(o.poly.bounds[2]))
        r = math.hypot(xmax, max(abs(o.y0), abs(o.y1)))
        if r > best:
            best, who = r, o.name
    for c in d.components:
        for x in c.x:
            for y in c.y:
                r = math.hypot(x, y)
                if r > best:
                    best, who = r, c.name
    return best, who


def link_masses(scale: float, throws: int, bp: BuildParams, density: float) -> dict[str, float]:
    """脚・フレーム・ピンの重量 [g]（板は外形の面積 x 板厚、穴は無視）。"""
    leg = JansenLeg(scale=scale)
    pose = _module_poses(leg, 0.3)
    parts = module_parts()
    links = sum(_shape(n, js, pose, leg, bp).area for n, js in parts.items()) * bp.plate * density
    la, ll = leg.length("a"), leg.length("l")
    r = bp.link_width / 2
    frame_area = MultiPoint([(-la, -ll), (la, -ll), (0, 0), (-la, bp.spacer_y), (la, bp.spacer_y)]).convex_hull.buffer(r + 1).area
    web_area = LineString([(0, 0), (leg.length("m"), 0)]).buffer(r + 1).area
    lay = solve_layers(leg, bp)
    n_modules = 2 * throws
    pitch = bp.plate + bp.washer
    # 各関節のピンの長さ = つなぐ部品の層の範囲 + 抜け止め 3 mm
    joints: dict[str, list[int]] = {}
    for name, js in parts.items():
        for j in js:
            if j not in ("P", "P'"):
                joints.setdefault(j, []).append(lay.layers[name])
    pin_lengths = []
    for j, ls in joints.items():
        if j == "A":
            span = lay.n_layers + 2  # ウェブ間を通す
        elif j in ("B", "B'"):
            side = lay.fixed_pin_side[j]
            span = (lay.n_layers + 2 - min(ls)) if side == "high" else (max(ls) + 1)  # フレーム板から片持ち
        else:
            span = max(ls) - min(ls) + 1
        pin_lengths.append(span * pitch + 3)
    pins = sum(math.pi * 1.5 ** 2 * length * STEEL_DENSITY + 0.2 for length in pin_lengths)  # φ3 + E リング
    return {
        "脚リンク": links * n_modules,
        "フレーム板": frame_area * bp.plate * density * 2 * (throws + 1),
        "クランクウェブ": web_area * bp.plate * density * 2 * n_modules,
        "ピン・E リング": pins * n_modules,
        "六角シャフト・スペーサ・ネジ": 12.0,
        "配線・コネクタ": 6.0,
        "足のゴム": 0.2 * 4 * n_modules,
    }


def support_half_width(d: BodyDesign, n: int = 180) -> float:
    """横方向の最小支持幅の半分 [mm]: クランク 1 回転のうち、接地している足の最も外側の横位置が最も内側に来るとき。

    左右のクランクは独立に回るので、片側ずつの最悪値をとる。
    """
    from .gait import LegMount, foot_position

    leg = JansenLeg(scale=d.scale)
    lay = solve_layers(leg, d.build)
    pitch = d.build.plate + d.build.washer
    module_t = (lay.n_layers + 2) * pitch + d.build.plate
    feet = []  # (クランク位相, 鏡像か, 横位置)
    for m in range(d.throws):
        base = d.center_width / 2 + d.build.plate + m * module_t
        for name, mirror in (("T", False), ("T'", True)):
            feet.append((360.0 * m / d.throws, mirror, base + (lay.layers[name] + 0.5) * pitch))
    worst = math.inf
    for i in range(n):
        th = 2 * math.pi * i / n
        ys = [foot_position(leg, th, LegMount(ph, mir))[1] for ph, mir, _ in feet]
        low = min(ys)
        outer = max(lat for (ph, mir, lat), y in zip(feet, ys) if y <= low + 0.5)
        worst = min(worst, outer)
    return worst


@dataclass
class BodyReport:
    interference: list[str]
    blockers: dict[str, list[str]]
    legacy_blockers: dict[str, list[str]]
    turning_radius: float
    turning_limiter: str
    mass_items: dict[str, float]
    total_mass: float
    cog: tuple[float, float, float]
    min_ground_clearance: float
    support_half_width: float
    tip_angle_deg: float


def evaluate(d: BodyDesign, density: float = 1.41e-3) -> BodyReport:
    obs, h = leg_obstacles(d.scale, d.throws, d.center_width, d.build)
    radius, who = turning_radius(d, obs)
    items = link_masses(d.scale, d.throws, d.build, density)
    items.update({c.name: c.mass_g for c in d.components})
    total = sum(items.values())
    # 重心: 部品は各々の中心、脚・フレーム類はクランク軸の高さに集中しているとみなす
    legs_mass = sum(v for k, v in items.items() if k not in {c.name for c in d.components})
    sx = sum(c.mass_g * c.center()[0] for c in d.components)
    sy = sum(c.mass_g * c.center()[1] for c in d.components)
    sz = sum(c.mass_g * c.center()[2] for c in d.components) + legs_mass * h
    cog = (sx / total, sy / total, sz / total)
    support_half = support_half_width(d)
    tip = math.degrees(math.atan2(support_half - abs(cog[1]), cog[2]))
    return BodyReport(
        interference=component_interference(d, obs),
        blockers=sensor_blockers(d, obs),
        legacy_blockers=sensor_blockers(BodyDesign(d.scale, d.throws, d.center_width, d.build), obs, legacy_sensors()),
        turning_radius=radius, turning_limiter=who,
        mass_items=items, total_mass=total, cog=cog,
        min_ground_clearance=min(c.z[0] for c in d.components),
        support_half_width=support_half,
        tip_angle_deg=tip,
    )
