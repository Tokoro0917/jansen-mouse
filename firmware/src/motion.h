// 1 kHz 制御ループで動く走行制御。
// 歩行機構はタイヤより滑りやすいため、向きは常にジャイロで閉ループ制御し、
// 距離のみをクランク回転数（x 1 回転あたりの前進量）から求める。
#pragma once

#include <stdint.h>

#include "pid.h"
#include "trapezoid.h"

class Motion {
 public:
  void begin();
  void tick();  // タイマ割り込みから呼ぶ

  // 以下はメインループから呼ぶ非ブロッキング指令
  void straight(float mm, float v_max, bool wall_centering);
  void turn(float deg);  // 反時計回り（左）が正
  void alignFront();     // 前壁を使って距離と向きを補正
  void stop();
  bool busy() const { return mode_ != Mode::kIdle; }
  void wait() const;

  float yawDeg() const { return yaw_; }
  float distanceMm() const;  // 左右クランク平均の走行距離

 private:
  enum class Mode : uint8_t { kIdle, kStraight, kTurn, kAlign };

  void drive(float v_mm_s, float w_deg_s);

  volatile Mode mode_ = Mode::kIdle;
  control::Trapezoid profile_;
  control::Pid pid_l_{0, 0, 0, 1}, pid_r_{0, 0, 0, 1};
  float yaw_ = 0.0f;
  float target_yaw_ = 0.0f;
  float turn_start_yaw_ = 0.0f;
  bool wall_centering_ = false;
  int32_t prev_enc_l_ = 0, prev_enc_r_ = 0;
  float rps_l_ = 0.0f, rps_r_ = 0.0f;  // クランク回転速度（ローパス後）
  float sens_l_ = 0.0f, sens_r_ = 0.0f;
  int settle_ticks_ = 0;
};

extern Motion motion;
