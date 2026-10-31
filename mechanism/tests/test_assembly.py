import pytest

from jansen import JansenLeg
from jansen.assembly import (BuildParams, footprint, max_part_height, module_parts, solve_layers,
                             verify_layout, web_clears_fixed_pins)
from jansen.cli import CENTER_WIDTH, CORRIDOR_MM, DEFAULT_SCALE, DEFAULT_THROWS

BP = BuildParams()


@pytest.fixture(scope="module")
def layout():
    return solve_layers(JansenLeg(scale=DEFAULT_SCALE), BP)


def test_every_part_gets_a_layer(layout):
    assert set(layout.layers) == set(module_parts())
    assert all(1 <= z <= layout.n_layers for z in layout.layers.values())


def test_layout_has_no_interference(layout):
    assert verify_layout(JansenLeg(scale=DEFAULT_SCALE), layout, BP) == []


def test_verify_detects_a_bad_layout(layout):
    bad = dict(layout.layers)
    bad["j"] = bad["U"]  # 関節 C を共有する部品を同じ層に置く
    broken = type(layout)(bad, layout.n_layers, layout.fixed_pin_side, layout.thickness, layout.length)
    assert verify_layout(JansenLeg(scale=DEFAULT_SCALE), broken, BP)


def test_robot_can_spin_inside_corridor():
    fp = footprint(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BP)
    assert fp.diagonal < CORRIDOR_MM - 15.0  # 位置ずれを見込んだ余裕


def test_sixteen_legs_do_not_fit():
    # 片側 4 スロー（16 脚）はどの縮尺でも、旋回半径の余裕が 8 mm 未満になる（設計判断の根拠）
    from jansen.body import BodyDesign, leg_obstacles, turning_radius

    for scale in (0.35, 0.40):
        obs, _ = leg_obstacles(scale, 4, CENTER_WIDTH, BP)
        radius, _ = turning_radius(BodyDesign(scale, 4, CENTER_WIDTH, BP), obs)
        assert 84.0 - radius < 8.0


def test_spacers_and_webs_clear_the_legs():
    leg = JansenLeg(scale=DEFAULT_SCALE)
    assert max_part_height(leg, BP) < BP.spacer_y - BP.spacer_radius
    assert web_clears_fixed_pins(leg, BP) > 0.5
