"""機構パラメータの解析・出力ツール。

    python -m jansen.cli report                 # 歩容指標とリンク長表を表示
    python -m jansen.cli plot  -o out/          # 足先軌跡・接地数のグラフ
    python -m jansen.cli anim  -o out/          # 動作アニメーション (GIF)
    python -m jansen.cli header -o ../firmware/include/mechanism_params.h
    python -m jansen.cli scad  -o ../cad/links_generated.scad
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from .gait import standard_side, support_analysis
from .linkage import HOLY_NUMBERS, MOVING_LINKS, JansenLeg, gait_metrics

DEFAULT_SCALE = 0.55   # [mm/unit] クラシックマウス (18cm 区画) 向け
DEFAULT_THROWS = 3     # 片側のクランクスロー数（脚は 2 倍）
CELL_MM = 180.0

# 関節図の線分（描画用）
SEGMENTS = [("O", "A"), ("A", "C"), ("B", "C"), ("A", "D"), ("B", "D"), ("B", "E"),
            ("C", "E"), ("E", "F"), ("D", "F"), ("F", "P"), ("D", "P")]


def build_report(scale: float, throws: int) -> str:
    leg = JansenLeg(scale=scale)
    g = gait_metrics(leg)
    sup = support_analysis(leg, standard_side(throws))
    lines = [
        f"# Jansen leg report (scale = {scale} mm/unit, throws/side = {throws})",
        "",
        "## 歩容",
        f"- ストライド（1回転あたり前進量）: {g.stride:.2f} mm",
        f"- 1区画 ({CELL_MM:.0f} mm) あたりクランク回転数: {CELL_MM / g.stride:.3f} rev",
        f"- 足上げ高さ: {g.step_height:.2f} mm",
        f"- クランク中心の対地高さ: {-g.ground_y:.2f} mm",
        f"- 接地区間の平坦度: {g.flatness:.3f} mm",
        f"- 足先の x 範囲: {g.x_min:.1f} 〜 {g.x_max:.1f} mm",
        f"- 片側の最小接地脚数: {sup.min_contacts}",
        f"- 胴体の上下動: {sup.body_bob:.3f} mm",
        "",
        "## リンク長 [mm]（穴中心間距離）",
        "",
        "| link | holy number | length |",
        "|---|---|---|",
    ]
    for name in sorted(HOLY_NUMBERS):
        kind = "" if name in MOVING_LINKS else "（フレーム）"
        lines.append(f"| {name}{kind} | {HOLY_NUMBERS[name]} | {leg.length(name):.2f} |")
    return "\n".join(lines) + "\n"


def cmd_plot(scale: float, throws: int, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    leg = JansenLeg(scale=scale)
    path = leg.foot_path(360)
    sup = support_analysis(leg, standard_side(throws))
    out.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(path[:, 0], path[:, 1], label="foot path")
    pts = leg.solve(math.radians(60))
    for a, b in SEGMENTS:
        ax.plot([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]], "k-o", ms=3, lw=1.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"Jansen leg (scale {scale} mm/unit)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.savefig(out / "foot_path.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.step(sup.thetas * 180 / math.pi, sup.contacts, where="post")
    ax.set_xlabel("crank angle [deg]")
    ax.set_ylabel("feet on ground (one side)")
    ax.set_ylim(0, max(sup.contacts) + 1)
    ax.grid(alpha=0.3)
    fig.savefig(out / "contacts.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def cmd_anim(scale: float, out: Path, frames: int = 48) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    leg = JansenLeg(scale=scale)
    path = leg.foot_path(360)
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(path[:, 0], path[:, 1], color="tab:blue", alpha=0.5)
    lines = [ax.plot([], [], "k-o", ms=3)[0] for _ in SEGMENTS]
    ax.set_aspect("equal")
    ax.set_xlim(-50, 15)
    ax.set_ylim(-55, 25)
    ax.grid(alpha=0.3)

    def update(k):
        pts = leg.solve(2 * math.pi * k / frames)
        for ln, (a, b) in zip(lines, SEGMENTS):
            ln.set_data([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]])
        return lines

    anim = FuncAnimation(fig, update, frames=frames, blit=True)
    anim.save(out / "leg.gif", writer=PillowWriter(fps=24))
    plt.close(fig)


def build_header(scale: float, throws: int) -> str:
    leg = JansenLeg(scale=scale)
    g = gait_metrics(leg)
    return f"""// このファイルは mechanism/ の `python -m jansen.cli header` で自動生成される。手で編集しないこと。
#pragma once

namespace mech {{
constexpr float kLinkScaleMmPerUnit = {scale:.4f}f;
constexpr int kCrankThrowsPerSide = {throws};
constexpr float kStrideMmPerRev = {g.stride:.4f}f;     // クランク1回転あたりの前進量
constexpr float kCrankHeightMm = {-g.ground_y:.4f}f;   // クランク中心の対地高さ
constexpr float kStepHeightMm = {g.step_height:.4f}f;
}}  // namespace mech
"""


def build_scad(scale: float) -> str:
    leg = JansenLeg(scale=scale)
    body = "\n".join(f"L_{n} = {leg.length(n):.3f};" for n in sorted(HOLY_NUMBERS))
    return ("// 自動生成: python -m jansen.cli scad （手で編集しないこと）\n"
            f"SCALE = {scale};\n{body}\n")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="jansen")
    p.add_argument("command", choices=["report", "plot", "anim", "header", "scad"])
    p.add_argument("--scale", type=float, default=DEFAULT_SCALE)
    p.add_argument("--throws", type=int, default=DEFAULT_THROWS)
    p.add_argument("-o", "--out", type=Path, default=None)
    args = p.parse_args(argv)

    if args.command == "report":
        text = build_report(args.scale, args.throws)
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        print(text, end="")
    elif args.command == "plot":
        cmd_plot(args.scale, args.throws, args.out or Path("out"))
    elif args.command == "anim":
        cmd_anim(args.scale, args.out or Path("out"))
    elif args.command == "header":
        text = build_header(args.scale, args.throws)
        (args.out.write_text(text, encoding="utf-8") if args.out else print(text, end=""))
    elif args.command == "scad":
        text = build_scad(args.scale)
        (args.out.write_text(text, encoding="utf-8") if args.out else print(text, end=""))


if __name__ == "__main__":
    main()
