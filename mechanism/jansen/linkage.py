"""テオヤンセン機構の運動学計算。

座標系: クランク中心 O を原点、x 右・y 上。脚は -x 側に伸びる（左向きの脚）。
リンク長は Theo Jansen の「Holy Numbers」を基準とし、scale [mm/unit] で実寸に換算する。

関節の命名（Wikipedia の図に準拠）:
    O : クランク中心（固定）
    B : 第2固定点 (-a, -l)
    A : クランク先端（半径 m）
    C : j と b の結合点（上側）
    D : k と c の結合点（下側）
    E : d と e の結合点（上三角形の左端）
    F : f と g の結合点
    P : 足先（h と i の結合点）
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# Theo Jansen の Holy Numbers（無次元）
HOLY_NUMBERS: dict[str, float] = {
    "a": 38.0, "b": 41.5, "c": 39.3, "d": 40.1, "e": 55.8, "f": 39.4,
    "g": 36.7, "h": 65.7, "i": 49.0, "j": 50.0, "k": 61.9, "l": 7.8, "m": 15.0,
}

# 実際に部品として作る可動リンク（a, l は固定点間距離なのでフレーム側）
MOVING_LINKS = ("b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m")


class LinkageError(ValueError):
    """リンクが閉じない（円が交わらない）姿勢。"""


def circle_intersection(p0, r0, p1, r1, pick: str) -> np.ndarray:
    """2円の交点のうち pick で指定した側を返す。

    pick: "up" / "down" は y の大小、"west" / "east" は x の大小で選ぶ。
    """
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    d_vec = p1 - p0
    d = math.hypot(*d_vec)
    if d > r0 + r1 or d < abs(r0 - r1) or d == 0.0:
        raise LinkageError(f"circles do not intersect: d={d:.3f}, r0={r0}, r1={r1}")
    a = (r0 * r0 - r1 * r1 + d * d) / (2.0 * d)
    h = math.sqrt(max(r0 * r0 - a * a, 0.0))
    base = p0 + a * d_vec / d
    perp = np.array([-d_vec[1], d_vec[0]]) / d
    q1 = base + h * perp
    q2 = base - h * perp
    axis, want_max = {"up": (1, True), "down": (1, False),
                      "east": (0, True), "west": (0, False)}[pick]
    if (q1[axis] > q2[axis]) == want_max:
        return q1
    return q2


@dataclass
class JansenLeg:
    """1本の脚。dims は無次元（Holy Numbers 系）、scale を掛けて mm になる。"""

    scale: float = 0.5
    dims: dict[str, float] = field(default_factory=lambda: dict(HOLY_NUMBERS))

    def length(self, name: str) -> float:
        return self.dims[name] * self.scale

    def solve(self, theta: float) -> dict[str, np.ndarray]:
        """クランク角 theta [rad]（x 軸から反時計回り）での全関節座標 [mm]。"""
        L = self.length
        O = np.array([0.0, 0.0])
        B = np.array([-L("a"), -L("l")])
        A = O + L("m") * np.array([math.cos(theta), math.sin(theta)])
        C = circle_intersection(A, L("j"), B, L("b"), "up")     # 上側ロッカー
        D = circle_intersection(A, L("k"), B, L("c"), "down")   # 下側ロッカー
        E = circle_intersection(B, L("d"), C, L("e"), "west")   # 上三角形の左端
        F = circle_intersection(E, L("f"), D, L("g"), "west")   # 足三角形の上端
        P = circle_intersection(F, L("h"), D, L("i"), "down")   # 足先
        return {"O": O, "B": B, "A": A, "C": C, "D": D, "E": E, "F": F, "P": P}

    def foot_path(self, n: int = 360) -> np.ndarray:
        """クランク1回転分の足先軌跡 (n, 2) [mm]。theta = 2πk/n。"""
        thetas = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        return np.array([self.solve(t)["P"] for t in thetas])


@dataclass
class GaitMetrics:
    stride: float           # 接地区間の水平移動量 [mm]（= クランク1回転あたりの前進量）
    step_height: float      # 足上げ高さ [mm]
    ground_fraction: float  # 接地とみなせる区間のクランク角比率
    flatness: float         # 接地区間の y の最大偏差 [mm]
    ground_y: float         # 接地面の y 座標（クランク中心基準）[mm]
    x_min: float
    x_max: float


def gait_metrics(leg: JansenLeg, n: int = 720, tol_ratio: float = 0.03) -> GaitMetrics:
    """足先軌跡から歩容の指標を求める。

    接地判定は「最下点から step_height * tol_ratio 以内」の区間。
    """
    path = leg.foot_path(n)
    y = path[:, 1]
    x = path[:, 0]
    y_min, y_max = y.min(), y.max()
    step_height = y_max - y_min
    ground = y <= y_min + step_height * tol_ratio
    stride = x[ground].max() - x[ground].min()
    return GaitMetrics(
        stride=float(stride),
        step_height=float(step_height),
        ground_fraction=float(ground.mean()),
        flatness=float(y[ground].max() - y_min),
        ground_y=float(y_min),
        x_min=float(x.min()),
        x_max=float(x.max()),
    )


def mirrored(points: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """前後反転（x -> -x）した脚。左右対称ペアを作るのに使う。"""
    return {k: np.array([-v[0], v[1]]) for k, v in points.items()}
