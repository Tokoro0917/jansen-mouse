"""部品ごとの表（docs/parts_list.md）を、機構の寸法・積層順・機体の配置から作る。

板の部品・3D プリント部品・ピンとスペーサ・軸とネジを、1 モジュール（前後 2 本の脚）と 1 台分の数で出す。
寸法を変えたら `python -m jansen.cli parts -o ../docs/parts_list.md` で作り直す。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .assembly import BuildParams, module_parts, solve_layers
from .body import HOLDER_D, HOLDER_W, holder_dims, default_design
from .linkage import JansenLeg

HOLE = 3.2           # ピン穴（cad/parts.scad の HOLE）
RETAIN = 1.5         # ピンの抜け止め（E リングの溝）に片側で要る長さ [mm]
LINK_NAME = {"j": "リンク j", "k": "リンク k", "c": "リンク c", "f": "リンク f",
             "U": "上三角形", "T": "足三角形"}
SCAD_PART = {"j": "bar_j", "k": "bar_k", "c": "bar_c", "f": "bar_f", "U": "tri_upper", "T": "tri_foot"}


@dataclass
class PinSpec:
    joint: str
    members: list[tuple[int, str]]   # (層, 部品)。層 0 / N+1 はクランクウェブ、N+2 / -1 はフレーム板
    length: float                    # ピンの長さ [mm]
    sleeves: list[float]             # 部品の間の空いた層を埋めるスリーブの長さ [mm]
    washers: int
    note: str


def _apex(s01: float, s02: float, s12: float) -> tuple[float, float]:
    x = (s02 * s02 - s12 * s12 + s01 * s01) / (2 * s01)
    return x, math.sqrt(s02 * s02 - x * x)


def _tri_size(leg: JansenLeg, a: str, b: str, c: str, w: float) -> tuple[float, float]:
    """cad/parts.scad の tri_plate の外形（外接長方形）。"""
    s01, s02, s12 = leg.length(a), leg.length(b), leg.length(c)
    px, py = _apex(s01, s02, s12)
    xs = [0.0, s01, px]
    return max(xs) - min(xs) + w, py + w


def pin_specs(leg: JansenLeg, bp: BuildParams) -> list[PinSpec]:
    lay = solve_layers(leg, bp)
    n = lay.n_layers
    pitch = bp.plate + bp.washer
    joints: dict[str, list[tuple[int, str]]] = {}
    for name, js in module_parts().items():
        for j in js:
            if j not in ("P", "P'"):
                joints.setdefault(j, []).append((lay.layers[name], name))
    out = []
    for j in sorted(joints, key=lambda s: (s.rstrip("'"), s.endswith("'"))):
        m = sorted(joints[j])
        if j == "A":
            m = [(0, "ウェブ")] + m + [(n + 1, "ウェブ")]
            note = "クランクピン。両端をクランクウェブに圧入（抜け止めなし）"
        elif j in ("B", "B'"):
            frame = n + 2 if lay.fixed_pin_side[j] == "high" else -1
            m = sorted(m + [(frame, "フレーム板")])
            note = "フレーム板から片持ちで立てる固定ピン"
        else:
            note = ""
        ls = [l for l, _ in m]
        grip = (ls[-1] - ls[0]) * pitch + bp.plate
        length = grip if j == "A" else grip + 2 * RETAIN
        sleeves = [(b - a) * pitch - bp.plate - bp.washer for a, b in zip(ls, ls[1:]) if b - a > 1]
        out.append(PinSpec(j, m, length, sleeves, len(ls) - 1, note))
    return out


def build_parts_list(scale: float, throws: int, center_width: float, bp: BuildParams) -> str:
    leg = JansenLeg(scale=scale)
    lay = solve_layers(leg, bp)
    n = lay.n_layers
    pitch = bp.plate + bp.washer
    w = bp.link_width
    modules = 2 * throws
    d = default_design(scale, throws, center_width, bp)
    comp = {c.name: c for c in d.components}
    lines = [
        "# 部品ごとの表",
        "",
        "自動生成: `python -m jansen.cli parts -o ../docs/parts_list.md`（寸法・積層順を変えたら作り直す）。",
        f"脚 {modules * 2} 本 = 片側 {throws} モジュール × 左右。1 モジュール = 前の脚 + 後ろの脚（前後に裏返した同じ部品）。",
        f"板厚 {bp.plate} mm、部品の間のワッシャ {bp.washer} mm（1 層 {pitch:.1f} mm）、リンク幅 {w} mm、ピン穴 φ{HOLE}。",
        "積層順は [design.md](design.md#22-組立クランク軸と積層順)、3D プリントは [printing.md](printing.md)。",
        "",
        "![脚どうしのつなぎ方](images/joints.png)",
        "",
        "## 1. 板の部品（脚・クランク・フレーム）",
        "",
        "| 部品 | ファイル（`cad/print/`） | 外形 [mm] | 穴 | 層 | 1 モジュール | 1 台 |",
        "|---|---|---|---|---|---|---|",
    ]
    # リンク（前の脚と後ろの脚で層が違う）
    for base in ("j", "k", "c", "f"):
        ln = leg.length(base)
        layers = f"{lay.layers[base]}（後ろ {lay.layers[base + chr(39)]}）"
        lines.append(f"| {LINK_NAME[base]} | `{SCAD_PART[base]}.stl` | {ln + w:.1f} × {w:.1f} | "
                     f"φ{HOLE} × 2（中心間 {ln:.2f}） | {layers} | 2 | {2 * modules} |")
    ux, uy = _tri_size(leg, "b", "d", "e", w)
    tx, ty = _tri_size(leg, "g", "i", "h", w)
    lines.append(f"| 上三角形（B・C・E） | `tri_upper.stl` | {ux:.1f} × {uy:.1f} | φ{HOLE} × 3"
                 f"（辺 {leg.length('b'):.2f} / {leg.length('d'):.2f} / {leg.length('e'):.2f}） | "
                 f"{lay.layers['U']}（後ろ {lay.layers[chr(85) + chr(39)]}） | 2 | {2 * modules} |")
    lines.append(f"| 足三角形（D・F・足先） | `tri_foot.stl` | {tx:.1f} × {ty:.1f} | φ{HOLE} × 2"
                 f"（辺 {leg.length('g'):.2f} / {leg.length('i'):.2f} / {leg.length('h'):.2f}）。足先にゴム | "
                 f"{lay.layers['T']}（後ろ {lay.layers['T' + chr(39)]}） | 2 | {2 * modules} |")
    m = leg.length("m")
    lines.append(f"| クランクウェブ | `web.stl` | {m + (w + 2) / 2 + w / 2:.1f} × {w + 2:.1f} | "
                 f"六角穴（3 mm 六角シャフト）+ クランクピン圧入穴 φ2.9（中心間 {m:.2f}） | 0 と {n + 1} | 2 | {2 * modules - 2} |")
    lines.append(f"| クランクウェブ（モータ軸用） | `web_motor.stl` | 同上 | D カット穴（モータ軸 φ3）+ φ2.9 | 0（いちばん内側） | — | 2 |")
    la, ll = leg.length("a"), leg.length("l")
    fw = 2 * la + w + 2
    fh = bp.spacer_y + 3.5 + ll + (w + 2) / 2
    lines.append(f"| フレーム板 | `frame.stl` | 約 {fw:.1f} × {fh:.1f} | 軸受 φ3.8、固定ピン φ{HOLE} × 2、"
                 f"タイロッド φ2.2 × 2 | モジュールの間 | — | {2 * (throws + 1)} |")
    lines += [
        "",
        f"板の部品の合計: リンク・三角形 {12 * modules} 個、クランクウェブ {2 * modules} 枚、フレーム板 {2 * (throws + 1)} 枚。",
        "",
        "## 2. 3D プリントの部品（機体）",
        "",
        "| 部品 | ファイル | 外形 [mm] | 数 | 備考 |",
        "|---|---|---|---|---|",
    ]
    b = comp["bridge"]
    lines.append(f"| ブリッジ | `print_bridge.stl` | {b.x[1] - b.x[0]:.1f} × {b.y[1] - b.y[0]:.1f} × {b.z[1] - b.z[0]:.1f} | 1 | "
                 "左右の内側フレーム板をつなぎ、モータを上から押さえ、上面に基板を留める。天板を下にして刷る |")
    mc = comp["motor_L"]
    lines.append(f"| モータ押さえ | `print_motor_clamp.stl` | {mc.x[1] - mc.x[0] + 14:.1f} × {b.y[1] - b.y[0]:.1f} × "
                 f"{b.z[0] - mc.z[0] + 2:.1f} | 1 | モータを下から支え、柱をブリッジのボスにネジ止め |")
    hh = holder_dims(comp["deck"].z[0])[0]
    lines.append(f"| 壁センサのホルダ | `print_sensor_holder.stl` | {HOLDER_W:.1f} × {HOLDER_D:.2f} × {hh:.1f} | 4 | "
                 "黒（光を通さない）。本番は光造形を推奨 |")
    lines += [
        "",
        "## 3. ピンとスペーサ（1 モジュールあたり）",
        "",
        f"ピンは φ3 の丸棒（ステンレス / 鋼）。長さ = つなぐ部品の範囲 + 抜け止め（E リングの溝）片側 {RETAIN} mm。"
        "途中で空いている層は、内径 3.2・外径 4 mm 以下のスリーブで埋める（脚の層は外径 4 mm のピンで干渉を確認している）。",
        "",
        "| 関節 | つなぐ部品（層） | ピンの長さ | スリーブ | ワッシャ | 備考 |",
        "|---|---|---|---|---|---|",
    ]
    pins = pin_specs(leg, bp)
    for p in pins:
        mem = "、".join(f"{LINK_NAME.get(nm.rstrip(chr(39)), nm)}{chr(39) if nm.endswith(chr(39)) else ''}（{l}）"
                       for l, nm in p.members)
        sl = "、".join(f"{s:.1f} mm" for s in p.sleeves) or "—"
        lines.append(f"| {p.joint} | {mem} | {p.length:.1f} mm | {sl} | {p.washers} | {p.note} |")
    by_len: dict[float, int] = {}
    for p in pins:
        if p.joint != "A":
            by_len[round(p.length, 1)] = by_len.get(round(p.length, 1), 0) + 1
    sleeves: dict[float, int] = {}
    for p in pins:
        for s in p.sleeves:
            sleeves[round(s, 1)] = sleeves.get(round(s, 1), 0) + 1
    crank = next(p for p in pins if p.joint == "A")
    n_washer = sum(p.washers for p in pins)
    n_ering = sum(2 for p in pins if p.joint != "A")  # ピンの両端（クランクピンは圧入）
    lines += [
        "",
        "1 台分（× " + str(modules) + " モジュール）:",
        "",
        "| もの | 長さ | 数 |",
        "|---|---|---|",
    ]
    for ln in sorted(by_len):
        lines.append(f"| φ3 ピン | {ln:.1f} mm | {by_len[ln] * modules} |")
    lines.append(f"| φ3 クランクピン | {crank.length:.1f} mm | {modules} |")
    for s in sorted(sleeves):
        lines.append(f"| スリーブ（内径 3.2） | {s:.1f} mm | {sleeves[s] * modules} |")
    lines.append(f"| ワッシャ（φ3 用、厚さ {bp.washer} mm） | — | {n_washer * modules} |")
    lines.append(f"| E リング（φ3 軸用） | — | {n_ering * modules} |")
    # 軸・タイロッド・ネジ
    from .body import leg_obstacles
    obs, h = leg_obstacles(scale, throws, center_width, bp)
    y_out = max(abs(o.y1) for o in obs)
    module_gap = (n + 2) * pitch
    hex_len = 3 * bp.plate + 2 * bp.washer
    clamp_h = b.z[0] - (mc.z[0] - 2.0)
    lines += [
        "",
        "## 4. 軸・タイロッド・ネジ（1 台）",
        "",
        "| もの | 寸法 | 数 | 備考 |",
        "|---|---|---|---|",
        f"| 3 mm 六角シャフト | 長さ {hex_len:.1f} mm | {2 * (throws - 1)} | モジュールの間のつなぎ（ウェブ + フレーム板 + ウェブ）。"
        "六角穴で 120° ずつ位相を合わせる。短いのでウェブの六角穴に接着する |",
        f"| M2 全ねじ（タイロッド） | 約 {2 * y_out + 8:.0f} mm | 2 | 左右すべてのフレーム板とブリッジを貫く |",
        f"| M2 ナット | — | 4 | タイロッドの両端 |",
        f"| タイロッドのスリーブ（内径 2.2） | {module_gap - bp.washer:.1f} mm | {2 * 2 * throws} | フレーム板の間（1 モジュールの厚さ）|",
        f"| M2 ネジ（基板 → ブリッジ） | 長さ 5 mm 前後 | 4 | ブリッジの下穴 φ1.8 にねじ込む |",
        f"| M2 ネジ（モータ押さえ → ブリッジ） | 長さ 約 {clamp_h + 5:.0f} mm | 2 | モータ押さえの柱を下から通す |",
        "| 足のゴム | ゴムシート / 熱収縮チューブ | " + str(4 * throws) + " | 足三角形の足先 |",
        "",
        "電装部品（マイコン・モータ・センサ・電池など）は [hardware.md](hardware.md#部品表1-台分の目安) の部品表を参照。",
        "",
    ]
    return "\n".join(lines)
