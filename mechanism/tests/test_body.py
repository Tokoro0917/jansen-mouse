import pytest

from jansen.body import default_design, evaluate
from jansen.cli import BUILD, CENTER_WIDTH, DEFAULT_SCALE, DEFAULT_THROWS, MASS_KG, build_header


@pytest.fixture(scope="module")
def report():
    return evaluate(default_design(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BUILD))


def test_components_do_not_hit_legs_or_each_other(report):
    assert report.interference == []


def test_wall_sensors_have_clear_line_of_sight(report):
    assert all(not b for b in report.blockers.values()), report.blockers


def test_previous_sensor_layout_is_blocked_by_legs(report):
    # 以前の配置は脚の掃引域を通っていた（この設計変更の理由）
    assert all(report.legacy_blockers.values())


def test_robot_can_spin_between_walls(report):
    assert report.turning_radius < 84.0 - 10.0


def test_mass_matches_the_torque_assumption(report):
    # 駆動トルクの見積もり（MASS_KG）を 10 % 以上超えないこと
    assert report.total_mass < MASS_KG * 1000 * 1.1


def test_stability_and_clearance(report):
    assert report.tip_angle_deg > 25.0
    assert report.min_ground_clearance > 10.0  # 床の継ぎ目・足上げ高さより上


def test_header_exports_sensor_geometry():
    h = build_header(DEFAULT_SCALE, DEFAULT_THROWS)
    for name in ("kFrontSensorForwardMm", "kFrontSensorLateralMm", "kSideSensorForwardMm", "kSideSensorLateralMm"):
        assert name in h
