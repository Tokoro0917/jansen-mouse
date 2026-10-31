#pragma once

#include <math.h>

namespace control {

// 台形速度プロファイル。距離・角度どちらにも使う（単位は呼び出し側で統一）。
// 終端速度 0 で停止する前提（区画中心で止まる歩行マウス向け）。
class Trapezoid {
 public:
  void start(float distance, float v_max, float accel) {
    sign_ = distance < 0 ? -1.0f : 1.0f;
    total_ = fabsf(distance);
    v_max_ = v_max;
    accel_ = accel;
    pos_ = 0.0f;
    vel_ = 0.0f;
    done_ = total_ <= 0.0f;
  }

  // dt 秒進めて現在の目標速度（符号つき）を返す。
  float update(float dt) {
    if (done_) return 0.0f;
    const float remaining = total_ - pos_;
    const float v_brake = sqrtf(2.0f * accel_ * remaining);  // ここから減速すれば止まれる速度
    float v = vel_ + accel_ * dt;
    if (v > v_max_) v = v_max_;
    if (v > v_brake) v = v_brake;
    // 低速域で止まりきらないのを防ぐ最小速度
    const float v_min = accel_ * dt;
    if (v < v_min) v = v_min;
    vel_ = v;
    pos_ += v * dt;
    if (pos_ >= total_) {
      pos_ = total_;
      vel_ = 0.0f;
      done_ = true;
    }
    return sign_ * vel_;
  }

  float position() const { return sign_ * pos_; }
  bool done() const { return done_; }

 private:
  float total_ = 0, v_max_ = 0, accel_ = 0, pos_ = 0, vel_ = 0, sign_ = 1;
  bool done_ = true;
};

}  // namespace control
