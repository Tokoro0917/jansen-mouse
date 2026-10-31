// テオヤンセン脚の部品（3D プリント / レーザー加工用）
// 寸法・板厚・積層順は mechanism/ から自動生成した links_generated.scad を使う。
//   python -m jansen.cli scad -o ../cad/links_generated.scad
// PART を切り替えて STL / DXF を個別に書き出せる:
//   openscad -D 'PART="layout"' -o leg_layout.stl parts.scad
include <links_generated.scad>

PART = "layout";   // layout | bar | tri_upper | tri_foot | web | web_motor | frame | coupler
                   // | motor_clamp | rod_post | sensor_holder | board_outline | none

T = PLATE;         // 板厚 [mm]
W = LINK_W;        // リンク幅 [mm]
HOLE = 3.2;        // ピン穴（φ3 シャフト / M3 ネジ）
PIN_PRESS = 2.9;   // クランクピン圧入穴（ウェブ側）
HEX_AF = 3.15;     // 六角シャフト 3 mm（二面幅）+ 逃げ。60° 刻みで位相を変えられる
JOURNAL = 3.8;     // フレーム板の軸受穴（六角シャフトの対角 3.46 mm + 逃げ）
SPACER_HOLE = 2.2; // M2 スペーサ
$fn = 48;

module holes(pts, d = HOLE) { for (p = pts) translate(p) circle(d = d); }
module hex_hole(af) { circle(d = af / cos(30), $fn = 6); }

// 両端に穴のある直線リンク（j, k, c, f）
module bar(len) {
  linear_extrude(T) difference() {
    hull() { circle(d = W); translate([len, 0]) circle(d = W); }
    holes([[0, 0], [len, 0]]);
  }
}

// 3 辺長から三角形の第 3 頂点（原点・(s01,0) に対して）
function apex(s01, s02, s12) =
  let(x = (s02 * s02 - s12 * s12 + s01 * s01) / (2 * s01)) [x, sqrt(s02 * s02 - x * x)];

module tri_plate(s01, s02, s12, foot = false) {
  p2 = apex(s01, s02, s12);
  linear_extrude(T) difference() {
    hull() { circle(d = W); translate([s01, 0]) circle(d = W); translate(p2) circle(d = W); }
    holes(foot ? [[0, 0], [s01, 0]] : [[0, 0], [s01, 0], p2]);
  }
}

// 上三角形 B-C-E (b, d, e): B 原点, C=(b,0), E は第 3 頂点
module tri_upper() { tri_plate(L_b, L_d, L_e); }
// 足三角形 D-F-P (g, i, h): D 原点, F=(g,0), P は足先（穴なし。ゴムを貼る）
module tri_foot() { tri_plate(L_g, L_i, L_h, foot = true); }

// クランクウェブ: 組立クランク軸の腕。O に六角穴、A にクランクピン圧入穴。
// 1 モジュールに 2 枚（脚の層の両側）。モジュール間の位相は六角穴で 60° 刻みに合わせる。
// motor = true は最も内側のウェブ用で、O にモータ出力軸（φ3 D カット）を直接差し込む。
module d_hole() { intersection() { circle(d = 3.1); translate([-2, -1.6]) square([4, 4.1]); } }
module web(motor = false) {
  linear_extrude(T) difference() {
    hull() { circle(d = W + 2); translate([L_m, 0]) circle(d = W); }
    if (motor) d_hole(); else hex_hole(HEX_AF);
    translate([L_m, 0]) circle(d = PIN_PRESS);
  }
}

// フレーム板: 軸受 O、前後の脚の固定ピン B / B'（鏡像）、タイロッド（M2 全ねじ）穴
module frame() {
  linear_extrude(T) difference() {
    hull() {
      translate([-L_a, -L_l]) circle(d = W + 2);
      translate([L_a, -L_l]) circle(d = W + 2);
      circle(d = W + 4);
      for (sx = [-1, 1]) translate([sx * L_a, SPACER_Y]) circle(d = 7);
    }
    circle(d = JOURNAL);
    holes([[-L_a, -L_l], [L_a, -L_l]]);
    for (sx = [-1, 1]) translate([sx * L_a, SPACER_Y]) circle(d = SPACER_HOLE);
  }
}

// ================================================================ 機体
// 以下は機体座標（x 前, y 左, z 上。床が z = 0、クランク軸が x = 0, z = CRANK_H）で描く。
//
// 構造: 2 本の M2 全ねじ（タイロッド）が、左右すべてのフレーム板・スペーサ（中央の溝ではスリーブ）を
// (x = ±L_a, z = CRANK_H + SPACER_Y) で横に貫き、最も外側のフレーム板の外からナットで締める。
TIE_Z = CRANK_H + SPACER_Y;
WALL = 2.0;
POST_D = 6.0;   // 柱の太さ

// 基板は 1 枚（KOGUMA Mk4 と同じく壁センサも同じ基板）。壁の高さ 50 mm より下に壁センサの光を出すため、
// 脚が入らない中央の溝の中、モータのすぐ上に置く。モータは基板とモータ押さえで上下から挟む。
// 基板はタイロッドの柱 2 本でタイロッドに留める。

// モータ押さえ（3D プリント）: 2 個のモータを下から支え、前後の柱を基板にネジ止めする
module motor_clamp() {
  wid = BOARD_Y[1] - BOARD_Y[0];
  difference() {
    union() {
      translate([CLAMP_POST_X[0] - 3, BOARD_Y[0], CLAMP_Z[0]]) cube([CLAMP_POST_X[1] - CLAMP_POST_X[0] + 6, wid, WALL]);
      for (x = CLAMP_POST_X) translate([x, 0, CLAMP_Z[0]]) cylinder(d = 5, h = BOARD_Z[0] - CLAMP_Z[0]);
    }
    for (x = CLAMP_POST_X) translate([x, 0, CLAMP_Z[0] + WALL]) cylinder(d = 1.8, h = 40);  // M2 タップ下穴（基板の上から留める）
  }
}

// タイロッドの柱（3D プリント）: 基板の上面から立ち、上端の横穴にタイロッド（M2 全ねじ）を通す
module rod_post() {
  hgt = TIE_Z - BOARD_Z[1] + 3;
  difference() {
    union() {
      cylinder(d = POST_D, h = hgt - 3);
      translate([0, 0, hgt - 3]) rotate([90, 0, 0]) cylinder(d = POST_D, h = POST_D, center = true);
    }
    translate([0, 0, hgt - 3]) rotate([90, 0, 0]) cylinder(d = SPACER_HOLE, h = POST_D + 2, center = true);
    translate([0, 0, -0.1]) cylinder(d = 1.8, h = 6);  // 基板の裏から M2 で留める
  }
}

module rod_posts() { for (sx = [-1, 1]) translate([sx * L_a, 0, BOARD_Z[1]]) rod_post(); }

// モータ軸（N20: φ3 D カット）→ 六角シャフト 3 mm の継手（web_motor を使えば不要。予備）
module coupler() {
  difference() {
    cylinder(d = 8, h = 12);
    translate([0, 0, -0.1]) linear_extrude(6.1) intersection() {
      circle(d = 3.1); translate([-2, -1.6]) square([4, 4.1]);  // D カット（平面 2.5 mm）
    }
    translate([0, 0, 6]) linear_extrude(6.1) hex_hole(HEX_AF);
  }
}

// 壁センサのホルダ（KOGUMA Mk4 / ToraNeko.Mk3 と同じ考え方。光を通さない黒い樹脂で作る）
// 基板の裏にさかさまに付ける。光は +x 向き。基板の面が z = 0、ホルダは z < 0 に下がる。
// 発光 OPV332 を基板から遠い穴、受光 SFH 229 FA を近い穴に後ろから差し、足を基板側に曲げて基板の穴に通す。
module sensor_holder() {
  w = HOLDER[0]; d = HOLDER[1]; hgt = HOLDER[2];
  difference() {
    union() {
      translate([-d, -w / 2, -hgt]) cube([d, w, hgt]);
      translate([-d, -1.5, 0]) cube([3.0, 3.0, 0.8]);  // ほぞ（基板の穴 3.2 x 3.2 に差す）
    }
    for (z = [HOLDER[3], HOLDER[4]]) translate([-d - 1, 0, -z]) rotate([0, 90, 0]) cylinder(d = 3.2, h = d + 2);
  }
}

// 4 個のホルダを機体座標に置く（基板の下面 BOARD_Z[0] から下げる）
module placed_holders() {
  for (s = SENSORS) translate([s[0], s[1], BOARD_Z[0]]) rotate([0, 0, s[2]]) sensor_holder();
}

// 基板の外形（2D。基板 CAD に読み込む DXF 用）: モータ押さえの柱・タイロッドの柱のネジ穴と、
// 壁センサのホルダのほぞの穴 3.2 x 3.2 を含む
module board_outline() {
  difference() {
    translate([BOARD_X[0], BOARD_Y[0]]) square([BOARD_X[1] - BOARD_X[0], BOARD_Y[1] - BOARD_Y[0]]);
    for (x = CLAMP_POST_X) translate([x, 0]) circle(d = 2.2);
    for (sx = [-1, 1]) translate([sx * L_a, 0]) circle(d = 2.2);
    for (s = SENSORS) translate([s[0], s[1]]) rotate(s[2]) translate([-HOLDER[1] + 1.5, 0]) square([3.2, 3.2], center = true);
  }
}

if (PART == "bar") bar(L_j);
if (PART == "tri_upper") tri_upper();
if (PART == "tri_foot") tri_foot();
if (PART == "web") web();
if (PART == "web_motor") web(motor = true);
if (PART == "frame") frame();
if (PART == "coupler") coupler();
if (PART == "rod_post") rod_post();
if (PART == "motor_clamp") motor_clamp();
if (PART == "sensor_holder") sensor_holder();
if (PART == "board_outline") board_outline();
if (PART == "layout") {
  // 脚 1 本分の部品一式（j, k, c, f の 4 本のバー + 三角形 2 枚）
  lens = [L_j, L_k, L_c, L_f];
  for (n = [0 : 3]) translate([0, n * (W + 3)]) bar(lens[n]);
  translate([0, 45]) tri_upper();
  translate([40, 45]) tri_foot();
}
