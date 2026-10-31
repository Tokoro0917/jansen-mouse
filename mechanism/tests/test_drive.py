import math

import numpy as np
import pytest

from jansen import JansenLeg, foot_position, gait_metrics, standard_side
from jansen.cli import DEFAULT_SCALE, DEFAULT_THROWS
from jansen.drive import crank_torque, drive_profile, spin_turn_torque


@pytest.fixture(scope="module")
def profile():
    return drive_profile(JansenLeg(scale=DEFAULT_SCALE), standard_side(DEFAULT_THROWS))


def planted_foot_travel(leg, mounts, n=2880):
    """速度を使わない別実装: 最も低い足を「地面に固定された点」とみなして胴体位置を追う。"""
    thetas = np.linspace(0, 2 * math.pi, n + 1)
    body_x = 0.0
    prev = [foot_position(leg, thetas[0], m) for m in mounts]
    for t in thetas[1:]:
        cur = [foot_position(leg, t, m) for m in mounts]
        k = int(np.argmin([p[1] for p in cur]))
        body_x += cur[k][0] - prev[k][0]  # 足が地面に対して動かない → 胴体が逆向きに動く
        prev = cur
    return body_x


def test_travel_per_rev_is_not_the_stance_length(profile):
    leg = JansenLeg(scale=DEFAULT_SCALE)
    independent = planted_foot_travel(leg, standard_side(DEFAULT_THROWS))
    # 接地足どうしの速度差（滑り）があるので完全一致はしないが、10 % 以内で一致する
    assert independent == pytest.approx(profile.travel_per_rev, rel=0.10)
    assert profile.travel_per_rev > 2.0 * gait_metrics(leg).stance_length


def test_travel_is_consistent_and_nearly_linear(profile):
    dth = profile.thetas[1] - profile.thetas[0]
    assert profile.travel_per_rev == pytest.approx(profile.body_speed.sum() * dth, rel=1e-3)
    assert np.all(np.diff(profile.travel) > 0)  # 常に前進
    linear = profile.thetas / (2 * math.pi) * profile.travel_per_rev
    assert np.abs(profile.travel - linear).max() < 1.5  # 回転角から線形に距離を出してよい


def test_travel_scales_with_leg_size():
    # 接地判定の許容差も同じ比率で拡大すれば、前進量は脚の大きさに比例する
    a = drive_profile(JansenLeg(scale=0.4), standard_side(2), n=720, contact_tol=0.2).travel_per_rev
    b = drive_profile(JansenLeg(scale=0.8), standard_side(2), n=720, contact_tol=0.4).travel_per_rev
    assert b == pytest.approx(2 * a, rel=1e-3)


def test_torque_estimates(profile):
    walk1 = crank_torque(profile, 0.2)
    walk2 = crank_torque(profile, 0.4)
    assert walk2.peak == pytest.approx(2 * walk1.peak, rel=1e-6)
    turn = spin_turn_torque(profile, 0.2, tread_mm=64.2)
    assert turn.peak > walk1.peak  # 旋回は横滑りの分だけ重い
    assert 1.0 < turn.peak < 50.0  # 桁の確認 [N·mm]
