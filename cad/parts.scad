// テオヤンセン脚の部品（3D プリント / レーザー加工用）
// 寸法・板厚・積層順は mechanism/ から自動生成した links_generated.scad を使う。
//   python -m jansen.cli scad -o ../cad/links_generated.scad
// PART を切り替えて STL / DXF を個別に書き出せる:
//   openscad -D 'PART="layout"' -o leg_layout.stl parts.scad
include <links_generated.scad>

PART = "layout";   // layout | bar | tri_upper | tri_foot | web | frame | coupler | none

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
module web() {
  linear_extrude(T) difference() {
    hull() { circle(d = W + 2); translate([L_m, 0]) circle(d = W); }
    hex_hole(HEX_AF);
    translate([L_m, 0]) circle(d = PIN_PRESS);
  }
}

// フレーム板: 軸受 O、前後の脚の固定ピン B / B'（鏡像）、スペーサ穴
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

// モータ軸（N20: φ3 D カット）→ 六角シャフト 3 mm の継手
module coupler() {
  difference() {
    cylinder(d = 8, h = 12);
    translate([0, 0, -0.1]) linear_extrude(6.1) intersection() {
      circle(d = 3.1); translate([-2, -1.6]) square([4, 4.1]);  // D カット（平面 2.5 mm）
    }
    translate([0, 0, 6]) linear_extrude(6.1) hex_hole(HEX_AF);
  }
}

if (PART == "bar") bar(L_j);
if (PART == "tri_upper") tri_upper();
if (PART == "tri_foot") tri_foot();
if (PART == "web") web();
if (PART == "frame") frame();
if (PART == "coupler") coupler();
if (PART == "layout") {
  // 脚 1 本分の部品一式（j, k, c, f の 4 本のバー + 三角形 2 枚）
  lens = [L_j, L_k, L_c, L_f];
  for (n = [0 : 3]) translate([0, n * (W + 3)]) bar(lens[n]);
  translate([0, 45]) tri_upper();
  translate([40, 45]) tri_foot();
}
