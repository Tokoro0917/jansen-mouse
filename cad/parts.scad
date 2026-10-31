// テオヤンセン脚の部品（3D プリント / レーザー加工用）
// リンク長は mechanism/ から自動生成した links_generated.scad を使う。
//   python -m jansen.cli scad -o ../cad/links_generated.scad
// PART を切り替えて STL を個別に書き出せる:
//   openscad -D 'PART="layout"' -o leg_layout.stl parts.scad
include <links_generated.scad>

PART = "layout";   // layout | bar | tri_upper | tri_foot | crank | frame

T = 3.0;           // 板厚 [mm]
W = 7.0;           // リンク幅 [mm]
HOLE = 3.2;        // ピン穴径（φ3 シャフト / M3 ネジ）
CRANK_BORE = 3.0;  // N20 出力軸（D カット φ3）
$fn = 48;

module holes(pts) { for (p = pts) translate(p) circle(d = HOLE); }

// 両端に穴のある直線リンク
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
    hull() { circle(d = W); translate([s01, 0]) circle(d = W); translate(p2) circle(d = foot ? W + 3 : W); }
    holes(foot ? [[0, 0], [s01, 0]] : [[0, 0], [s01, 0], p2]);
  }
}

// 上三角形 B-C-E (b, d, e): B 原点, C=(b,0), E は第 3 頂点
module tri_upper() { tri_plate(L_b, L_d, L_e); }
// 足三角形 D-F-P (g, i, h): D 原点, F=(g,0), P（足先）は穴なし・ゴム足を貼る
module tri_foot() { tri_plate(L_g, L_i, L_h, foot = true); }

// クランク: 3 スロー (120°) のクランクピン位置を持つ円板。中心はモータ軸。
module crank(throws = 3) {
  linear_extrude(T) difference() {
    circle(r = L_m + W / 2 + 1);
    circle(d = CRANK_BORE);
    for (k = [0 : throws - 1]) rotate(360 * k / throws) translate([L_m, 0]) circle(d = HOLE);
  }
}

// 側板: クランク軸 O と、前後の脚の固定点 B / B'（鏡像）
module frame() {
  linear_extrude(T) difference() {
    hull() {
      translate([-L_a, -L_l]) circle(d = W + 4);
      translate([L_a, -L_l]) circle(d = W + 4);
      circle(d = W + 8);
      translate([0, 25]) square([2 * L_a, 10], center = true);
    }
    circle(d = 4.0);  // クランク軸受
    holes([[-L_a, -L_l], [L_a, -L_l]]);
  }
}

if (PART == "bar") bar(L_j);
if (PART == "tri_upper") tri_upper();
if (PART == "tri_foot") tri_foot();
if (PART == "crank") crank();
if (PART == "frame") frame();
if (PART == "layout") {
  // 脚 1 本分の部品一式（j, k, c, f の 4 本のバー + 三角形 2 枚）
  lens = [L_j, L_k, L_c, L_f];
  for (n = [0 : 3]) translate([0, n * (W + 3)]) bar(lens[n]);
  translate([0, 50]) tri_upper();
  translate([50, 50]) tri_foot();
}
