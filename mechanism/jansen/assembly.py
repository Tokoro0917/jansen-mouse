"""脚モジュール（1 クランクスロー = 前後鏡像ペア）の積層順の決定と干渉チェック。

構造（片側 1 スロー分）:

    フレーム板 | クランクウェブ | 脚の層 1..N | クランクウェブ | フレーム板 ...

リンク j, k は回転中にクランク中心 O の上を通過するため、脚の層を貫く通し軸は置けない。
そこで自転車のクランク軸のように、2 枚のウェブの間にクランクピン A だけを渡す（組立クランク軸）。
固定ピン B / B' はどちらかのフレーム板から片持ちで立てる。

各部品は板として脚の層 1..N のどれかに置く。同じ層の部品同士がクランク 1 回転のどこかで
重なると干渉、また部品が自分の付いていないピンを横切る場合も（そのピンがその層を
貫いていれば）干渉とみなす。干渉のない、層数が最小の割り当てをバックトラックで探す。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import Point, LineString, MultiPoint
from shapely.ops import unary_union

from .linkage import JansenLeg

# 部品 -> その部品が持つ関節
PART_JOINTS: dict[str, tuple[str, ...]] = {
    "j": ("A", "C"),
    "k": ("A", "D"),
    "c": ("B", "D"),
    "f": ("E", "F"),
    "U": ("B", "C", "E"),   # 上三角形 (b, d, e)
    "T": ("D", "F", "P"),   # 足三角形 (g, i, h)
}
FIXED_JOINTS = ("B", "B'")  # フレームに固定される関節


@dataclass(frozen=True)
class BuildParams:
    link_width: float = 7.0      # リンク幅 [mm]
    plate: float = 1.5           # 板厚 [mm]（1.5 mm 厚 POM / アクリル）。12 脚を通路幅に収めるため
    washer: float = 0.3          # 層間ワッシャ [mm]
    pin_radius: float = 2.0      # ピン + 逃げ [mm]
    clearance: float = 0.6       # 同一層の部品間に最低限ほしい隙間 [mm]
    spacer_y: float = 21.0       # タイロッドの高さ（クランク中心基準）[mm]。脚の最高点（縮尺 0.40 で 17 mm）+ 余裕
    spacer_radius: float = 2.5   # M2 スペーサ + 逃げ [mm]
    samples: int = 72            # 1 回転あたりの姿勢サンプル数


@dataclass
class ModuleLayout:
    layers: dict[str, int]            # 部品名 -> 層番号（1..n_layers）
    n_layers: int
    fixed_pin_side: dict[str, str]    # 固定ピン -> 立てる側 ("low" / "high")
    thickness: float                  # ウェブ 2 枚・フレーム板 1 枚を含むモジュール厚 [mm]
    length: float                     # 前後方向の全長（脚の掃引範囲）[mm]
    extra: dict = field(default_factory=dict)


def _mirror(p):
    return (-p[0], p[1])


def _module_poses(leg: JansenLeg, theta: float) -> dict[str, tuple[float, float]]:
    """前脚 (無印) と後脚 (' 付き, 同じクランクピンを共有) の全関節座標。"""
    front = {k: tuple(v) for k, v in leg.solve(theta).items()}
    rear_src = leg.solve(math.pi - theta)
    rear = {k + "'": _mirror(tuple(v)) for k, v in rear_src.items()}
    return {**front, **rear}


def module_parts() -> dict[str, tuple[str, ...]]:
    parts: dict[str, tuple[str, ...]] = {}
    for name, joints in PART_JOINTS.items():
        parts[name] = joints
        parts[name + "'"] = tuple(("A" if j == "A" else j + "'") for j in joints)
    return parts


def _shape(name: str, joints, pose, leg: JansenLeg, bp: BuildParams):
    r = bp.link_width / 2
    pts = [pose[j] for j in joints]
    if len(pts) == 2:
        return LineString(pts).buffer(r)
    return MultiPoint(pts).convex_hull.buffer(r)


def _joints_of(parts) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for p, js in parts.items():
        for j in js:
            out.setdefault(j, set()).add(p)
    return out


def analyze_conflicts(leg: JansenLeg, bp: BuildParams):
    """部品同士・部品とピンの干渉の有無を、1 回転分のサンプルで調べる。"""
    parts = module_parts()
    joints = _joints_of(parts)
    names = list(parts)
    pair = {a: set() for a in names}
    pin_hit: dict[str, set[str]] = {j: set() for j in joints if j not in ("P", "P'")}
    xs: list[float] = []
    for s in range(bp.samples):
        pose = _module_poses(leg, 2 * math.pi * s / bp.samples)
        shapes = {n: _shape(n, parts[n], pose, leg, bp) for n in names}
        for n, sh in shapes.items():
            minx, _, maxx, _ = sh.bounds
            xs += [minx, maxx]
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if shapes[a].distance(shapes[b]) < bp.clearance:
                    pair[a].add(b)
                    pair[b].add(a)
        for j in pin_hit:
            pin = Point(pose[j]).buffer(bp.pin_radius)
            for n in names:
                if j not in parts[n] and shapes[n].intersects(pin):
                    pin_hit[j].add(n)
    return parts, joints, pair, pin_hit, (min(xs), max(xs))


def _pin_spans(joint: str, attached: set[str], layers: dict[str, int], top: int):
    """ピンが貫く層範囲の候補 [(lo, hi, side)]。いずれか 1 つが成立すればよい。"""
    if joint == "A":
        return [(1, top, "both")]  # クランクピンは両ウェブ間に渡す
    ls = [layers[p] for p in attached]
    lo, hi = min(ls), max(ls)
    if joint in FIXED_JOINTS:
        return [(1, hi, "low"), (lo, top, "high")]  # どちらかのフレーム板から片持ち
    return [(lo, hi, "none")]


def _pin_choice(joint, attached, layers, top, hits):
    """衝突しないピン配置を返す（なければ None）。"""
    for lo, hi, side in _pin_spans(joint, attached, layers, top):
        if not any(n in layers and lo <= layers[n] <= hi for n in hits):
            return lo, hi, side
    return None


def solve_layers(leg: JansenLeg, bp: BuildParams = BuildParams(), max_layers: int = 10) -> ModuleLayout:
    parts, joints, pair, pin_hit, (xmin, xmax) = analyze_conflicts(leg, bp)
    # 制約の強い部品から割り当てる
    order = sorted(parts, key=lambda n: -len(pair[n]))
    pins = {j: joints[j] for j in pin_hit}

    def pins_ok(layers, top):
        for j, attached in pins.items():
            if all(p in layers for p in attached) and \
                    _pin_choice(j, attached, layers, top, pin_hit[j]) is None:
                return False
        return True

    for n_layers in range(2, max_layers + 1):
        top = n_layers
        layers: dict[str, int] = {}

        def bt(i):
            if i == len(order):
                return True
            n = order[i]
            for z in range(1, n_layers + 1):
                if any(layers.get(o) == z for o in pair[n]):
                    continue
                layers[n] = z
                if pins_ok(layers, top) and bt(i + 1):
                    return True
                del layers[n]
            return False

        if bt(0):
            sides = {j: _pin_choice(j, joints[j], layers, top, pin_hit[j])[2] for j in FIXED_JOINTS}
            thickness = (n_layers + 2) * (bp.plate + bp.washer) + bp.plate
            return ModuleLayout(dict(layers), n_layers, sides, thickness, xmax - xmin,
                                extra={"x_range": (xmin, xmax)})
    raise RuntimeError("no feasible layer assignment")


def verify_layout(leg: JansenLeg, layout: ModuleLayout, bp: BuildParams = BuildParams()) -> list[str]:
    """割り当て結果を独立に再検査し、干渉の説明を返す（空なら OK）。"""
    parts, joints, pair, pin_hit, _ = analyze_conflicts(leg, bp)
    L = layout.layers
    top = layout.n_layers
    problems = []
    for a in parts:
        if not 1 <= L[a] <= top:
            problems.append(f"{a} の層 {L[a]} が範囲外")
        for b in pair[a]:
            if a < b and L[a] == L[b]:
                problems.append(f"{a} と {b} が層 {L[a]} で干渉")
    for j, hits in pin_hit.items():
        if _pin_choice(j, joints[j], L, top, hits) is None:
            problems.append(f"ピン {j} が他の部品と干渉")
    return problems


def max_part_height(leg: JansenLeg, bp: BuildParams = BuildParams()) -> float:
    """脚の部品が 1 回転中に到達する最高点 [mm]（スペーサとの干渉確認用）。"""
    parts = module_parts()
    top = -math.inf
    for s in range(bp.samples):
        pose = _module_poses(leg, 2 * math.pi * s / bp.samples)
        for n, js in parts.items():
            top = max(top, _shape(n, js, pose, leg, bp).bounds[3])
    return top


def web_clears_fixed_pins(leg: JansenLeg, bp: BuildParams = BuildParams()) -> float:
    """クランクウェブの回転範囲と固定ピン B の隙間 [mm]（正なら干渉なし）。"""
    web_reach = leg.length("m") + bp.link_width / 2
    ob = math.hypot(leg.length("a"), leg.length("l"))
    return ob - bp.pin_radius - web_reach


@dataclass
class Footprint:
    scale: float
    throws: int
    layout: ModuleLayout
    length: float      # 前後 [mm]
    width: float       # 左右 [mm]
    diagonal: float    # 超信地旋回時の掃引直径 [mm]


def footprint(scale: float, throws: int, center_width: float,
              bp: BuildParams = BuildParams()) -> Footprint:
    """機体全体の外形。幅 = 左右それぞれ (スロー数 x モジュール厚 + 外側フレーム板) + 中央部。"""
    leg = JansenLeg(scale=scale)
    layout = solve_layers(leg, bp)
    side = throws * layout.thickness + bp.plate
    width = 2 * side + center_width
    return Footprint(scale, throws, layout, layout.length, width, math.hypot(layout.length, width))
