import math

import numpy as np
import pytest

from jansen import HOLY_NUMBERS, JansenLeg, gait_metrics, standard_side, support_analysis
from jansen.cli import DEFAULT_SCALE, DEFAULT_THROWS, build_header, build_report

PAIRS = {  # 関節間に張られたリンク
    "m": ("O", "A"), "j": ("A", "C"), "b": ("B", "C"), "k": ("A", "D"), "c": ("B", "D"),
    "d": ("B", "E"), "e": ("C", "E"), "f": ("E", "F"), "g": ("D", "F"),
    "h": ("F", "P"), "i": ("D", "P"),
}


@pytest.mark.parametrize("theta", np.linspace(0, 2 * math.pi, 37))
def test_link_lengths_preserved(theta):
    leg = JansenLeg(scale=0.55)
    pts = leg.solve(theta)
    for name, (a, b) in PAIRS.items():
        assert np.linalg.norm(pts[a] - pts[b]) == pytest.approx(leg.length(name), abs=1e-9)


def test_joints_continuous_over_full_rotation():
    leg = JansenLeg(scale=1.0)
    thetas = np.linspace(0, 2 * math.pi, 1440, endpoint=False)
    sols = [leg.solve(t) for t in thetas]
    for joint in "CDEFP":
        arr = np.array([s[joint] for s in sols])
        steps = np.linalg.norm(np.diff(arr, axis=0), axis=1)
        assert steps.max() < 0.5, f"{joint} jumps (branch flip)"


def test_classic_jansen_gait_shape():
    g = gait_metrics(JansenLeg(scale=1.0))
    # Holy Numbers の既知の特徴: 平坦な接地区間と、クランク半径の 3 倍以上のストライド
    assert g.flatness < 1.0
    assert g.stride > 3 * HOLY_NUMBERS["m"]
    assert g.ground_y == pytest.approx(-91.8, abs=0.5)


def test_metrics_scale_linearly():
    g1 = gait_metrics(JansenLeg(scale=1.0))
    g2 = gait_metrics(JansenLeg(scale=0.5))
    assert g2.stride == pytest.approx(g1.stride * 0.5, rel=1e-6)
    assert g2.step_height == pytest.approx(g1.step_height * 0.5, rel=1e-6)


def test_default_config_keeps_two_feet_on_ground():
    rep = support_analysis(JansenLeg(scale=DEFAULT_SCALE), standard_side(DEFAULT_THROWS))
    assert rep.min_contacts >= 2
    assert rep.body_bob < 1.0
    # 3 スローにすると上下動はほぼ消える（外形の制約で不採用）
    assert support_analysis(JansenLeg(scale=DEFAULT_SCALE), standard_side(3)).body_bob < 0.1


def test_cli_outputs():
    assert "kStrideMmPerRev" in build_header(DEFAULT_SCALE, DEFAULT_THROWS)
    assert "| m |" in build_report(DEFAULT_SCALE, DEFAULT_THROWS)
