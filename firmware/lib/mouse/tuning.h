// 実機ごとに計測して決める壁センサの値。
// 実行時に変えられるようにしてある（シミュレーションでは模擬センサで計測した値を入れる）。
#pragma once

namespace mouse {

struct WallTuning {
  int thr_front = 180;       // (FL+FR)/2 がこれを超えたら前壁あり
  int thr_side = 220;        // L / R がこれを超えたら横壁あり
  int side_ref_l = 900;      // 区画中央にいるときの L（中央寄せの目標）
  int side_ref_r = 900;
  int front_ref_sum = 2600;  // 前壁ありで区画中央にいるときの FL+FR（前壁補正の目標）
};

}  // namespace mouse
