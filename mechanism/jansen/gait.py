"""複数脚の配置（クランク位相・前後反転）による接地状況の解析。"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .linkage import JansenLeg, mirrored


@dataclass(frozen=True)
class LegMount:
    """1本の脚の取り付け。phase: クランク位相 [deg]、mirror: 前後反転脚か。"""

    phase_deg: float
    mirror: bool = False


def standard_side(n_throws: int = 3) -> list[LegMount]:
    """片側の標準構成: n_throws 個のクランクスロー × 前後ペア。"""
    mounts = []
    for k in range(n_throws):
        ph = 360.0 * k / n_throws
        mounts.append(LegMount(ph, False))
        mounts.append(LegMount(ph, True))
    return mounts


def foot_position(leg: JansenLeg, theta: float, mount: LegMount) -> np.ndarray:
    th = theta + math.radians(mount.phase_deg)
    if not mount.mirror:
        return leg.solve(th)["P"]
    # 同じクランクピンを共有する反転脚は、ピン角度 π-θ の脚を x 反転したもの
    return mirrored(leg.solve(math.pi - th))["P"]


@dataclass
class SupportReport:
    min_contacts: int          # 1回転中の最小接地脚数
    body_bob: float            # 胴体の上下動 [mm]（最下点にある足で支持されると仮定）
    contacts: np.ndarray       # 各クランク角での接地脚数
    thetas: np.ndarray


def support_analysis(leg: JansenLeg, mounts: list[LegMount], n: int = 360,
                     contact_tol: float = 0.5) -> SupportReport:
    """クランク角ごとに接地脚数と胴体高さの変動を求める。

    contact_tol [mm]: 最下点の足から この範囲内にある足を接地とみなす。
    """
    thetas = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    contacts = np.zeros(n, dtype=int)
    lowest = np.zeros(n)
    for idx, th in enumerate(thetas):
        ys = np.array([foot_position(leg, th, m)[1] for m in mounts])
        lowest[idx] = ys.min()
        contacts[idx] = int((ys <= ys.min() + contact_tol).sum())
    return SupportReport(
        min_contacts=int(contacts.min()),
        body_bob=float(lowest.max() - lowest.min()),
        contacts=contacts,
        thetas=thetas,
    )
