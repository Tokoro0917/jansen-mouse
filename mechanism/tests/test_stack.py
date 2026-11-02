"""フレーム板とウェブの間に、どのモジュールでも両側にワッシャ 1 枚分の隙間があるか。"""
import re

import pytest

from jansen import JansenLeg
from jansen.assembly import layer_offset, module_thickness, solve_layers
from jansen.assembly_guide import side_scad
from jansen.body import leg_obstacles
from jansen.cli import BUILD, CENTER_WIDTH, DEFAULT_SCALE, DEFAULT_THROWS, build_assembly
from jansen.parts_list import build_parts_list, pin_specs

W = BUILD.washer
T = BUILD.plate


@pytest.fixture(scope="module")
def lay():
    return solve_layers(JansenLeg(scale=DEFAULT_SCALE), BUILD)


def _check_stack(frames, webs, n_modules):
    """frames / webs: 板の下面の位置（中央から外へ増える）。各モジュール: フレーム | ウェブ ... ウェブ | フレーム。"""
    frames, webs = sorted(frames), sorted(webs)
    assert len(frames) == n_modules + 1 and len(webs) == 2 * n_modules
    for m in range(n_modules):
        assert webs[2 * m] - (frames[m] + T) == pytest.approx(W)          # 内側: フレーム板 | ワッシャ | ウェブ
        assert frames[m + 1] - (webs[2 * m + 1] + T) == pytest.approx(W)  # 外側: ウェブ | ワッシャ | フレーム板


def test_module_thickness_counts_a_washer_on_both_frame_sides(lay):
    n = lay.n_layers
    plates = n + 3   # フレーム板 1 + ウェブ 2 + 脚 n
    washers = n + 3  # フレーム|w|ウェブ|w|脚1|...|脚n|w|ウェブ|w|次のフレーム
    assert lay.thickness == pytest.approx(plates * T + washers * W)
    assert lay.thickness == pytest.approx(module_thickness(n, BUILD))
    assert layer_offset(-1, BUILD) == 0
    assert layer_offset(n + 2, BUILD) == pytest.approx(lay.thickness)


def test_obstacles_leave_a_washer_between_frames_and_legs(lay):
    obs, _ = leg_obstacles(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BUILD)
    for side in "LR":
        frames = sorted((min(abs(o.y0), abs(o.y1)), max(abs(o.y0), abs(o.y1)))
                        for o in obs if o.name.startswith("frame") and o.name.endswith(side))
        legs = sorted((min(abs(o.y0), abs(o.y1)), max(abs(o.y0), abs(o.y1)))
                      for o in obs if o.name.startswith("legs") and o.name.endswith(side))
        assert len(legs) == DEFAULT_THROWS
        for m, (lo, hi) in enumerate(legs):
            assert lo - frames[m][1] == pytest.approx(W)
            assert frames[m + 1][0] - hi == pytest.approx(W)


def test_assembly_scad_stack(lay):
    text = build_assembly(DEFAULT_SCALE, DEFAULT_THROWS, 30.0)
    num = r"(-?[\d.]+)"
    frames = [float(z) for z in re.findall(rf"translate\(\[0,0,{num}\]\) frame\(\)", text)]
    webs = [float(w) for _, _, w in
            re.findall(rf"translate\(\[{num},{num},{num}\]\) rotate\([^)]*\) (?:mirror\(\[0,1,0\]\) )?web\(\)", text)]
    for sgn in (1, -1):
        # 右側（z < 0）は板の下面 = 外側の面なので、中央側の面 (|z| - 板厚) に直して比べる
        f = [z if sgn > 0 else -z - T for z in frames if z * sgn > 0]
        w = [z if sgn > 0 else -z - T for z in webs if z * sgn > 0]
        _check_stack(f, w, DEFAULT_THROWS)


def test_assembly_guide_side_view_stack():
    text = side_scad(JansenLeg(scale=DEFAULT_SCALE), BUILD, DEFAULT_THROWS, CENTER_WIDTH, 30.0, gap=0.0)
    num = r"(-?[\d.]+)"
    frames = [float(z) for z in re.findall(rf"translate\(\[0,0,{num}\]\) frame\(\)", text)]
    webs = [float(w) for _, _, w in
            re.findall(rf"translate\(\[{num},{num},{num}\]\) rotate\([^)]*\) web\([^)]*\)", text)]
    _check_stack(frames, webs, DEFAULT_THROWS)


def test_frame_pin_and_tie_rod_sleeve_match_the_stack(lay):
    n = lay.n_layers
    # 固定ピン B のフレーム板は層 -1 か N+2（どちらもウェブとの間にワッシャ 1 枚）
    for p in pin_specs(JansenLeg(scale=DEFAULT_SCALE), BUILD):
        for layer, name in p.members:
            if name == "フレーム板":
                assert layer in (-1, n + 2)
    text = build_parts_list(DEFAULT_SCALE, DEFAULT_THROWS, CENTER_WIDTH, BUILD)
    sleeve = re.search(r"タイロッドのスリーブ（内径 2.2） \| ([\d.]+) mm", text)
    assert float(sleeve.group(1)) == pytest.approx(lay.thickness - T, abs=0.05)
