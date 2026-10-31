// 1 kHz 制御ループで動く走行制御。
// 歩行機構はタイヤより滑りやすいため、向きは常にジャイロで閉ループ制御し、
// 距離のみをクランク回転数（x 1 回転あたりの前進量）から求める。
#pragma once

#include <stdint.h>

#include "mouse_io.h"
#include "pid.h"
#include "trapezoid.h"
#include "tuning.h"

namespace mouse {

class Motion {
 public:
  Motion(MouseIO& io, const WallTuning& tuning) : io_(io), tuning_(tuning) {}

  void begin();
  void tick();  // 制御周期ごとに呼ぶ（実機はタイマ割り込み）

  // 以下はメインループから呼ぶ非ブロッキング指令
  void straight(float mm, float v_max, bool wall_centering);
  float straightProgressMm() const;  // 今の直進で進んだ距離（壁切れ補正込み）
  void turn(float deg);  // 反時計回り（左）が正
  void alignFront();     // 前壁を使って距離と向きを補正
  void stop();
  bool busy() const { return mode_ != Mode::kIdle; }
  void wait();

  float yawDeg() const { return yaw_; }
  int wallEdgeCorrections() const { return edge_corrections_; }  // 壁切れで距離を補正した回数
  float distanceMm() const;  // 左右クランク平均の走行距離

 private:
  enum class Mode : uint8_t { kIdle, kStraight, kTurn, kAlign };

  void drive(float v_mm_s, float w_deg_s);
  void detectWallEdge(float value, bool* seen, float* seen_since_mm, float traveled_mm);
  void stopLocked();

  MouseIO& io_;
  const WallTuning& tuning_;
  volatile Mode mode_ = Mode::kIdle;
  control::Trapezoid profile_;
  control::Pid pid_l_{0, 0, 0, 1}, pid_r_{0, 0, 0, 1};
  float yaw_ = 0.0f;              // ジャイロ積分による向きの推定値 [deg]
  float heading_ref_ = 0.0f;      // 指令した旋回の累積（迷路に対する理想の向き）[deg]
  float wall_trim_ = 0.0f;        // 横壁から学習した向きの補正（ジャイロのドリフト分）[deg]
  float turn_start_ = 0.0f;
  float turn_goal_ = 0.0f;
  float straight_start_mm_ = 0.0f;  // 直進開始時のオドメトリ距離
  bool wall_centering_ = false;
  int32_t prev_enc_l_ = 0, prev_enc_r_ = 0;
  float rps_l_ = 0.0f, rps_r_ = 0.0f;  // クランク回転速度（ローパス後）
  float sens_l_ = 0.0f, sens_r_ = 0.0f;  // 中央寄せ用（強めのローパス）
  float edge_l_ = 0.0f, edge_r_ = 0.0f;  // 壁切れ検出用（遅れの小さいローパス）
  bool wall_seen_l_ = false, wall_seen_r_ = false;
  float seen_since_l_ = 0.0f, seen_since_r_ = 0.0f;  // 横壁が見え始めた走行距離
  int edge_corrections_ = 0;
  int settle_ticks_ = 0;
  int align_settled_ = 0;  // 前壁補正で目標に収まっている tick 数
};

}  // namespace mouse
