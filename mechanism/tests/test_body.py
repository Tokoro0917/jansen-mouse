import pytest

from jansen.body import Sensor, default_design, evaluate, leg_obstacles, sensor_blockers
from jansen.cli import BUILD, CENTER_WIDTH, DEFAULT_SCALE, DEFAULT_THROWS, MASS_KG, build_header


@pytest.fixture(scope="module")
def report():
    return evaluate(default_design(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BUILD))


def test_components_do_not_hit_legs_or_each_other(report):
    assert report.interference == []


def test_wall_sensors_have_clear_line_of_sight(report):
    assert all(not b for b in report.blockers.values()), report.blockers


def test_previous_sensor_layout_was_blocked_by_legs():
    # 最初の配置（8 脚・縮尺 0.45・板厚 2 mm のとき）は脚の掃引域を通っていた（この設計変更の理由）
    from dataclasses import replace

    old = evaluate(default_design(0.45, 2, CENTER_WIDTH, replace(BUILD, plate=2.0)))
    assert all(old.legacy_blockers.values())


def test_cone_check_catches_a_side_sensor_too_close_to_the_legs():
    d = default_design(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BUILD)
    obs, _ = leg_obstacles(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BUILD)
    # 光の高さで脚が届く前後の範囲を求め、その 3 mm 前に置く: 光の中心線は脚の前を通るが、円すい（±10°）は脚に当たる
    from shapely.geometry import box

    z = d.sensors[2].origin[2]
    band = box(-200, z - 1, 200, z + 1)
    reach = max(max(abs(o.poly.intersection(band).bounds[0]), abs(o.poly.intersection(band).bounds[2]))
                for o in obs if not o.poly.intersection(band).is_empty)
    near = Sensor("L(脚の近く)", (reach + 3.0, 13.0, z), 90.0, "")
    assert sensor_blockers(d, obs, [near])["L(脚の近く)"]
    far = Sensor("L(脚から離す)", (reach + 15.0, 13.0, z), 90.0, "")
    assert not sensor_blockers(d, obs, [far])["L(脚から離す)"]


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
