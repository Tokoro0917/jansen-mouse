"""買う部品を減らした試作キット（3D プリントの部品 + フィラメント + 接着剤だけで 1 モジュールを組む）。

本番（φ3 の金属ピン・ワッシャ・スリーブ・E リング・六角シャフト・タイロッド）の代わりに:
- ピン: 3D プリンタの 1.75 mm フィラメントを切って使う。端ははんだごてで潰して頭にするか、部品に接着して面一にする
- ワッシャ・スリーブ: 部品の穴のまわりの「ボス」（円筒の出っ張り）にして、部品と一緒に刷る
- クランク軸: 外側のウェブに六角の軸を一緒に刷る。内側は六角の軸 + つまみを刷る
- タイロッド: 内側のフレーム板に柱を一緒に刷り、外側のフレーム板に接着する

ボスは、部品の片面（層の番号が大きい側 = 固定ピンを立てるフレーム板の側）にだけ付ける。どの部品もボスを上にして
平らに刷れる。ボスの外径は 4 mm で、積層順を決めるときに確かめた「ピン + 逃げ φ4」の範囲に収まる。

    python -m jansen.cli kit -o ../cad/print_kit_generated.scad
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .assembly import BuildParams, _module_poses, module_parts, solve_layers
from .linkage import JansenLeg
from .parts_list import LINK_NAME, _sweepers, pin_specs

PIN_D = 1.75          # フィラメント
PIN_HOLE = 1.9        # ピン穴（設計値。FDM では FDM_CLEAR を足す）
BOSS_D = 4.0          # ボスの外径（積層順の確認に使ったピン + 逃げ φ4 と同じ）
BOSS_PLAY = 0.1       # ボスの高さを隙間より少し低くする（回るための遊び）
HEAD_R = 1.9          # 潰した頭の半径 + 逃げ（φ3.4 程度の頭）
HEAD_LEN = 1.0        # 頭を作るためにピンを出しておく長さ [mm]
HEX_AF = 3.0          # 印刷する六角軸の二面幅（ウェブの六角穴 3.15 + FDM_CLEAR に差す）
POST_D = 4.0          # タイロッドの代わりの柱の外径（タイロッドの位置で脚まで 4 mm ある）


@dataclass
class KitPart:
    name: str                       # ファイル名（kit_<name>.stl）
    label: str                      # 表の名前
    outline: list[tuple[float, float, float]]   # (x, y, 直径) の円の hull
    holes: list[tuple[float, float, str]]       # (x, y, 種類 "pin" / "hex" / "journal" / "tie" / "dcut")
    bosses: list[tuple[float, float, float]] = field(default_factory=list)  # (x, y, 高さ)
    hex_stub: tuple[float, float, float] | None = None   # (x, y, 長さ): 上面に六角軸
    posts: list[tuple[float, float, float]] = field(default_factory=list)   # (x, y, 長さ): 上面に柱 + 先にほぞ
    count: int = 1                  # 1 モジュールあたり


def boss_plan(leg: JansenLeg, bp: BuildParams) -> dict[tuple[str, str], float]:
    """{(部品, 関節): ボスの高さ}。隙間は下側（層の小さい側）の部品の上面のボスで埋める。"""
    pitch = bp.plate + bp.washer
    plan: dict[tuple[str, str], float] = {}
    for p in pin_specs(leg, bp):
        for (a, na), (b, _) in zip(p.members, p.members[1:]):
            owner = f"web{a}" if na == "ウェブ" else ("frame" if na == "フレーム板" else na)
            plan[(owner, p.joint)] = (b - a) * pitch - bp.plate - BOSS_PLAY
    return plan


def pin_plan(leg: JansenLeg, bp: BuildParams) -> list[dict]:
    """関節ごとのフィラメントのピン: 長さと、両端の処理（頭 / 面一・接着）。"""
    pitch = bp.plate + bp.washer
    out = []
    for p in pin_specs(leg, bp):
        ls = [m[0] for m in p.members]
        if p.joint == "A":
            ends = ("接着", "接着")
        else:
            near = _sweepers(leg, bp, p.joint, HEAD_R)
            ends = tuple("接着（面一）" if adj in near else "頭" for adj in (ls[0] - 1, ls[-1] + 1))
        grip = (ls[-1] - ls[0]) * pitch + bp.plate
        out.append({"joint": p.joint, "members": p.members, "ends": ends,
                    "length": grip + HEAD_LEN * sum(e == "頭" for e in ends)})
    return out


def kit_parts(leg: JansenLeg, bp: BuildParams) -> list[KitPart]:
    lay = solve_layers(leg, bp)
    n = lay.n_layers
    pitch = bp.plate + bp.washer
    w = bp.link_width
    pose = _module_poses(leg, 0.0)
    plan = boss_plan(leg, bp)
    parts: list[KitPart] = []

    def local(pts):
        x0, y0 = pts[0]
        return [(x - x0, y - y0) for x, y in pts]

    for name, js in module_parts().items():
        pts = local([tuple(pose[j]) for j in js])
        holes = [(x, y, "pin") for (x, y), j in zip(pts, js) if j not in ("P", "P'")]
        bosses = [(x, y, plan[(name, j)]) for (x, y), j in zip(pts, js) if (name, j) in plan]
        base = name.rstrip("'")
        label = LINK_NAME[base] + ("（後ろの脚）" if name.endswith("'") else "（前の脚）")
        parts.append(KitPart(f"{base}{'_back' if name.endswith(chr(39)) else '_front'}", label,
                             [(x, y, w) for x, y in pts], holes, bosses))
    # クランクウェブ（O を原点、A を +x）
    m = leg.length("m")
    a_boss0 = plan.get(("web0", "A"))
    parts.append(KitPart("web_inner", "クランクウェブ（内側。六角穴）", [(0, 0, w + 2), (m, 0, w)],
                         [(0, 0, "hex"), (m, 0, "pin")], [(m, 0, a_boss0)] if a_boss0 else []))
    stub = bp.washer + bp.plate + bp.washer + bp.plate   # フレーム板を抜けて、次のモジュールの内側ウェブまで
    parts.append(KitPart("web_outer", "クランクウェブ（外側。六角軸つき）", [(0, 0, w + 2), (m, 0, w)],
                         [(m, 0, "pin")], [], hex_stub=(0, 0, stub)))
    # フレーム板（O を原点）
    la, ll = leg.length("a"), leg.length("l")
    outline = [(-la, -ll, w + 2), (la, -ll, w + 2), (0, 0, w + 4), (-la, bp.spacer_y, 7), (la, bp.spacer_y, 7)]
    fholes = [(0, 0, "journal"), (-la, -ll, "pin"), (la, -ll, "pin"),
              (-la, bp.spacer_y, "tie"), (la, bp.spacer_y, "tie")]
    parts.append(KitPart("frame_outer", "フレーム板（外側。固定ピン B・B' を立てる）", outline, fholes))
    gap = (n + 3) * pitch - bp.plate       # 内側のフレーム板の上面 → 外側のフレーム板の下面
    parts.append(KitPart("frame_inner", "フレーム板（内側。柱つき）", outline, [h for h in fholes if h[2] != "tie"],
                         posts=[(-la, bp.spacer_y, gap), (la, bp.spacer_y, gap)]))
    # 試作用の内側の軸（内側のフレーム板の軸受を通して、内側のウェブの六角穴に差す。外につまみ）
    parts.append(KitPart("hex_axle", "六角軸 + つまみ（試作で手で回す）", [(0, 0, 10)], [], [],
                         hex_stub=(0, 0, bp.plate + bp.washer + bp.plate)))
    return parts


def build_kit_scad(leg: JansenLeg, bp: BuildParams) -> str:
    parts = kit_parts(leg, bp)
    t = bp.plate
    out = [
        "// 自動生成: python -m jansen.cli kit -o ../cad/print_kit_generated.scad （手で編集しないこと）",
        "// 買う部品を減らした試作キット（jansen/print_kit.py）。PART = 部品名 で 1 つずつ書き出す。",
        "PART = \"all\";",
        "FDM_CLEAR = 0.2;   // FDM で穴を大きくする分",
        f"T = {t};",
        f"PIN_HOLE = {PIN_HOLE} + FDM_CLEAR;",
        f"BOSS_D = {BOSS_D};",
        f"HEX_HOLE_AF = 3.15 + FDM_CLEAR;",
        f"HEX_AF = {HEX_AF};",
        f"JOURNAL = 3.8 + FDM_CLEAR;",
        f"TIE_HOLE = 2.2 + FDM_CLEAR;",
        f"POST_D = {POST_D};",
        "$fn = 40;",
        "module hexagon(af) { circle(d = af / cos(30), $fn = 6); }",
        "module hole(k) {",
        "  if (k == \"pin\") circle(d = PIN_HOLE);",
        "  if (k == \"hex\") hexagon(HEX_HOLE_AF);",
        "  if (k == \"journal\") circle(d = JOURNAL);",
        "  if (k == \"tie\") circle(d = TIE_HOLE);",
        "}",
    ]
    for p in parts:
        circles = " ".join(f"translate([{x:.3f},{y:.3f}]) circle(d = {d});" for x, y, d in p.outline)
        holes2d = " ".join(f"translate([{x:.3f},{y:.3f}]) hole(\"{k}\");" for x, y, k in p.holes)
        body = [f"module kit_{p.name}() {{", "  difference() {", "    union() {",
                f"      linear_extrude(T) hull() {{ {circles} }}"]
        for x, y, hgt in p.bosses:
            body.append(f"      translate([{x:.3f},{y:.3f},T]) cylinder(d = BOSS_D, h = {hgt:.2f});")
        if p.hex_stub:
            x, y, length = p.hex_stub
            body.append(f"      translate([{x:.3f},{y:.3f},T]) linear_extrude({length:.2f}) hexagon(HEX_AF);")
        for x, y, length in p.posts:
            body.append(f"      translate([{x:.3f},{y:.3f},T]) cylinder(d = POST_D, h = {length:.2f});")
            body.append(f"      translate([{x:.3f},{y:.3f},T + {length:.2f}]) cylinder(d = TIE_HOLE - 0.3, h = {t - 0.2:.2f});")
        body.append("    }")
        if holes2d:
            body.append(f"    translate([0,0,-1]) linear_extrude(50) {{ {holes2d} }}")
        body += ["  }", "}"]
        out += body
    out.append("// 1 モジュール分を並べて置く（PART = \"all\"）")
    for p in parts:
        out.append(f"if (PART == \"{p.name}\") kit_{p.name}();")
    out.append("if (PART == \"all\") {")
    for i, p in enumerate(parts):
        out.append(f"  translate([{(i % 5) * 55:.1f}, {-(i // 5) * 50:.1f}, 0]) kit_{p.name}();")
    out.append("}")
    # 組み上がりの確認用（PART = "assembled"）: 各部品を 1 モジュールの位置・層に置く
    lay = solve_layers(leg, bp)
    pitch = bp.plate + bp.washer
    pose = _module_poses(leg, 0.0)
    out.append("if (PART == \"assembled\") {")
    for name, js in module_parts().items():
        base = name.rstrip("'")
        x, y = pose[js[0]]
        kp = f"{base}{'_back' if name.endswith(chr(39)) else '_front'}"
        out.append(f"  translate([{x:.3f},{y:.3f},{lay.layers[name] * pitch:.3f}]) kit_{kp}();")
    ox, oy = pose["O"]
    n = lay.n_layers
    out.append(f"  translate([{ox:.3f},{oy:.3f},0]) kit_web_inner();")
    out.append(f"  translate([{ox:.3f},{oy:.3f},{(n + 1) * pitch:.3f}]) kit_web_outer();")
    out.append(f"  translate([{ox:.3f},{oy:.3f},{(n + 2) * pitch:.3f}]) kit_frame_outer();")
    out.append(f"  translate([{ox:.3f},{oy:.3f},{-pitch:.3f}]) kit_frame_inner();")
    out.append(f"  translate([{ox:.3f},{oy:.3f},{-pitch - bp.washer:.3f}]) mirror([0,0,1]) kit_hex_axle();")
    out.append("}")
    return "\n".join(out) + "\n"


def kit_table(leg: JansenLeg, bp: BuildParams) -> list[str]:
    parts = kit_parts(leg, bp)
    pins = pin_plan(leg, bp)
    lines = ["| ファイル（`cad/print/`） | 部品 | 1 組 | ボス（穴のまわりの出っ張り） |", "|---|---|---|---|"]
    for p in parts:
        b = "、".join(f"{h:.1f} mm" for _, _, h in p.bosses) or "—"
        extra = []
        if p.hex_stub:
            extra.append(f"六角軸 {p.hex_stub[2]:.1f} mm")
        if p.posts:
            extra.append(f"柱 {p.posts[0][2]:.1f} mm × {len(p.posts)}")
        lines.append(f"| `kit_{p.name}.stl` | {p.label} | {p.count} | {b}{'（' + '、'.join(extra) + '）' if extra else ''} |")
    lines += ["", "| 関節 | フィラメントの長さ | 端（層の小さい側 / 大きい側） |", "|---|---|---|"]
    for p in pins:
        lines.append(f"| {p['joint']} | {p['length']:.1f} mm | {p['ends'][0]} / {p['ends'][1]} |")
    total = sum(p["length"] for p in pins)
    lines += ["", f"フィラメントの合計: 約 {total:.0f} mm（1 組）。"]
    return lines
