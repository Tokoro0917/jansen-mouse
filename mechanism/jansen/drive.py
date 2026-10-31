"""歩行の駆動解析: クランク角と胴体移動量の関係、足の滑り、必要なクランクトルク。

注意: 1 回転あたりの前進量は「1 本の足の接地区間の長さ（gait_metrics の stance_length）」ではない。
複数の脚が交代で胴体を支えるので、胴体は常に「接地中の足の速度」で進み、
1 回転の前進量 = ∫ v_接地足 dθ になる（脚の接地率が 1 未満なら接地区間より長い）。

モデル（準静的・片側ずつ）:
- 接地足 = 最も低い足から contact_tol 以内の足。荷重は接地足で等分。
- 接地足の速度が食い違うときは、摩擦力の釣り合いから胴体はその平均速度で進み、各足は差の分だけ滑る。
- クランクトルク = 胴体を持ち上げる仕事 + 足の滑り摩擦の仕事（仮想仕事の原理）。
  関節の摩擦は link_efficiency でまとめて見込む。
- 超信地旋回: 脚は前後にしか足を動かせないので、接地足はクランク軸からの前後距離 |x| に比例した
  速さ ω|x| で横に滑る。その摩擦の仕事を左右のクランクが受け持つ。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .gait import LegMount, foot_position
from .linkage import JansenLeg

G = 9.81


@dataclass
class DriveProfile:
    thetas: np.ndarray        # クランク角 [rad]
    body_speed: np.ndarray    # dx/dθ [mm/rad]（胴体の前進速度 / クランク角速度）
    travel: np.ndarray        # θ=0 からの累積前進量 [mm]
    travel_per_rev: float     # 1 回転あたりの前進量 [mm]
    body_height: np.ndarray   # クランク中心の対地高さ [mm]
    slip: np.ndarray          # 接地足の滑り速度の合計 [mm/rad]
    foot_reach: np.ndarray    # 接地足のクランク軸からの前後距離 |x| の平均 [mm]


def drive_profile(leg: JansenLeg, mounts: list[LegMount], n: int = 1440,
                  contact_tol: float = 0.3) -> DriveProfile:
    thetas = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
    dth = 2 * math.pi / n
    P = np.array([[foot_position(leg, t, m) for m in mounts] for t in thetas])  # (n, legs, 2)
    dP = (np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)) / (2 * dth)
    speed = np.empty(n)
    slip = np.empty(n)
    height = np.empty(n)
    reach = np.empty(n)
    for i in range(n):
        ys = P[i, :, 1]
        grounded = ys <= ys.min() + contact_tol
        v = dP[i, grounded, 0]
        speed[i] = v.mean()
        slip[i] = np.abs(v - speed[i]).sum()
        height[i] = -ys.min()
        reach[i] = np.abs(P[i, grounded, 0]).mean()
    travel = np.concatenate([[0.0], np.cumsum(0.5 * (speed + np.roll(speed, -1)) * dth)])
    return DriveProfile(thetas, speed, travel[:-1], float(travel[-1]), height, slip, reach)


@dataclass
class TorqueEstimate:
    peak: float     # 片側クランク軸の最大トルク [N·mm]
    rms: float      # 実効値 [N·mm]
    lift_peak: float
    scuff_peak: float


def crank_torque(profile: DriveProfile, mass_kg: float, n_feet_grounded_hint: int = 2,
                 mu: float = 0.6, link_efficiency: float = 0.6) -> TorqueEstimate:
    """片側のクランク軸に必要なトルク。荷重は機体重量の半分。

    mu: 足（ゴム）と床の摩擦係数。link_efficiency: 関節摩擦をまとめた効率。
    """
    w_side = mass_kg * G / 2.0  # [N]
    dth = profile.thetas[1] - profile.thetas[0]
    dh = (np.roll(profile.body_height, -1) - np.roll(profile.body_height, 1)) / (2 * dth)
    lift = w_side * np.clip(dh, 0.0, None)  # 持ち上げにはトルクが要る（下降分は回収しない）
    # 滑り摩擦: 接地足 1 本あたりの荷重 = w_side / 接地本数（ここでは典型値で近似）
    scuff = mu * (w_side / n_feet_grounded_hint) * profile.slip
    total = (lift + scuff) / link_efficiency
    return TorqueEstimate(float(total.max()), float(np.sqrt((total ** 2).mean())),
                          float(lift.max()), float(scuff.max()))


def spin_turn_torque(profile: DriveProfile, mass_kg: float, tread_mm: float,
                     mu: float = 0.6, link_efficiency: float = 0.6) -> TorqueEstimate:
    """超信地旋回時の片側クランクトルク。

    ヨー角速度 ω のとき接地足は横に ω|x| で滑る。摩擦の仕事率 μ·Mg·ω·|x| を
    左右 2 本のクランク（角速度 θ' = ω·T / (2·v_b)）で受け持つので、
    τ = μ·Mg·|x|·v_b / T。直進時の項（持ち上げ・前後の滑り）も加える。
    """
    straight = crank_torque(profile, mass_kg, mu=mu, link_efficiency=1.0)
    lateral = mu * mass_kg * G * profile.foot_reach * profile.body_speed / tread_mm
    w_side = mass_kg * G / 2.0
    dth = profile.thetas[1] - profile.thetas[0]
    dh = (np.roll(profile.body_height, -1) - np.roll(profile.body_height, 1)) / (2 * dth)
    base = w_side * np.clip(dh, 0.0, None) + mu * (w_side / 2) * profile.slip
    total = (lateral + base) / link_efficiency
    return TorqueEstimate(float(total.max()), float(np.sqrt((total ** 2).mean())),
                          straight.lift_peak, float(lateral.max()))
