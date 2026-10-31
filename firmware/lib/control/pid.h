#pragma once

namespace control {

// 積分飽和防止つき PID。dt は秒。
class Pid {
 public:
  Pid(float kp, float ki, float kd, float out_limit)
      : kp_(kp), ki_(ki), kd_(kd), limit_(out_limit) {}

  void reset() {
    integral_ = 0.0f;
    prev_error_ = 0.0f;
    first_ = true;
  }

  float update(float error, float dt) {
    const float deriv = first_ ? 0.0f : (error - prev_error_) / dt;
    first_ = false;
    prev_error_ = error;
    const float candidate = integral_ + error * dt;
    float out = kp_ * error + ki_ * candidate + kd_ * deriv;
    // 出力が飽和していない、または積分が飽和を緩める方向のときだけ積分する
    if ((out < limit_ && out > -limit_) || (out >= limit_ && error < 0) ||
        (out <= -limit_ && error > 0)) {
      integral_ = candidate;
    }
    out = kp_ * error + ki_ * integral_ + kd_ * deriv;
    if (out > limit_) out = limit_;
    if (out < -limit_) out = -limit_;
    return out;
  }

 private:
  float kp_, ki_, kd_, limit_;
  float integral_ = 0.0f;
  float prev_error_ = 0.0f;
  bool first_ = true;
};

}  // namespace control
