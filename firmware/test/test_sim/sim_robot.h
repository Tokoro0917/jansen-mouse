// PC 上で歩行マウスを模擬する mouse::MouseIO 実装。
// 実機と同じ Motion / Runner を、この模擬ロボットの上で 1 kHz で動かす。
//
// 模擬するもの:
//  - モータ: duty -> クランク角速度の 1 次遅れ
//  - 歩行: 胴体速度 = クランク角速度 x 胴体速度表（1 回転内の ±27 % の揺れ）x 前進量の誤差
//  - 旋回: 左右の速度差から。足の横滑りで実効が落ちる（turn_efficiency）
//  - 向きの外乱（脚の滑りによるランダムなヨー）とジャイロのバイアス・ノイズ
//  - 赤外壁センサ: 壁・柱へのレイキャストで距離を求め、K (r0/d)^2 で ADC 値にする
//  - 衝突: 機体外形（103 x 102 mm）が壁・柱に入ったら記録する
#pragma once

#include <math.h>
#include <stdint.h>

#include "config.h"
#include "maze.h"
#include "motion.h"
#include "mouse_io.h"

#ifndef SIDE_ANGLE
#define SIDE_ANGLE 90  // 左右センサの向き [deg]（-DSIDE_ANGLE=60 で斜め前向きと比較できる）
#endif

namespace sim {

constexpr float kPi = 3.14159265f;

struct SimParams {
  float travel_scale = 1.0f;      // 実際の前進量 / モデルの前進量（較正の残差）
  float turn_efficiency = 0.75f;  // 旋回時の実効（足の横滑り）
  float yaw_disturbance_dps = 3.0f;  // 歩行中のランダムなヨー外乱（標準偏差相当）
  float gyro_bias_dps = 0.2f;     // 較正後に残るバイアス
  float gyro_noise_dps = 0.5f;
  float motor_tau_s = 0.03f;
  float sensor_noise = 15.0f;
  uint32_t seed = 12345;
};

struct Rect {
  float x0, y0, x1, y1;
};

class SimRobot : public mouse::MouseIO {
 public:
  // 機体外形（脚の掃引範囲）とセンサ配置 [mm]（前 = +f, 左 = +l）
  static constexpr float kHalfLength = mech::kBodyLengthMm / 2;
  static constexpr float kHalfWidth = mech::kBodyWidthMm / 2;
  struct Sensor {
    float f, l, angle_deg;
  };
  static constexpr Sensor kSensors[4] = {
      {45, 20, 0},     // FL
      {cfg::kSideSensorForwardMm, 15, SIDE_ANGLE},    // L
      {cfg::kSideSensorForwardMm, -15, -SIDE_ANGLE},  // R
      {45, -20, 0},    // FR
  };

  SimRobot(const maze::Maze& truth, SimParams p) : truth_(truth), p_(p), rng_(p.seed) {
    placeAtCell(0, 0, 90.0f);
  }

  void attach(mouse::Motion* m) { motion_ = m; }

  void placeAtCell(int cx, int cy, float heading_deg) {
    x_ = 90.0f + 180.0f * cx;
    y_ = 90.0f + 180.0f * cy;
    th_ = heading_deg * kPi / 180.0f;
  }

  // ---- MouseIO ----
  void motorsSet(float l, float r) override {
    duty_l_ = l;
    duty_r_ = r;
  }
  void motorsBrake() override { duty_l_ = duty_r_ = 0.0f; }
  int32_t encoderLeft() const override { return counts(phi_l_); }
  int32_t encoderRight() const override { return counts(phi_r_); }
  void wallSensorsSample() override {
    // 実機と同じく前方 / 側方を交互に更新
    if (sample_front_) {
      reading_.fl = sense(0);
      reading_.fr = sense(3);
    } else {
      reading_.l = sense(1);
      reading_.r = sense(2);
    }
    sample_front_ = !sample_front_;
  }
  mouse::WallReading wallSensors() const override { return reading_; }
  float yawRateDps() override {
    return true_yaw_rate_ * 180.0f / kPi + p_.gyro_bias_dps + p_.gyro_noise_dps * gauss();
  }
  float batteryVolts() const override { return 7.6f; }
  void delayMs(int ms) override {
    for (int i = 0; i < ms; ++i) {
      if (motion_) motion_->tick();
      step(cfg::kDt);
      time_s_ += cfg::kDt;
    }
  }
  void lock() override {}
  void unlock() override {}

  // ---- 観測 ----
  float x() const { return x_; }
  float y() const { return y_; }
  float headingDeg() const { return th_ * 180.0f / kPi; }
  float timeS() const { return time_s_; }
  int collisions() const { return collisions_; }
  // いる区画と、区画中心からのずれ [mm]
  int cellX() const { return static_cast<int>(floorf(x_ / 180.0f)); }
  int cellY() const { return static_cast<int>(floorf(y_ / 180.0f)); }
  float offsetFromCellCenter() const {
    return hypotf(x_ - (90.0f + 180.0f * cellX()), y_ - (90.0f + 180.0f * cellY()));
  }

 private:
  int32_t counts(float phi) const {
    return static_cast<int32_t>(lroundf(phi / (2 * kPi) * cfg::kCountsPerCrankRev));
  }

  float bodySpeed(float phi) const {  // [mm/rad]
    float u = fmodf(phi, 2 * kPi);
    if (u < 0) u += 2 * kPi;
    const float pos = u / (2 * kPi) * mech::kBodySpeedTableSize;
    const int i0 = static_cast<int>(pos) % mech::kBodySpeedTableSize;
    const int i1 = (i0 + 1) % mech::kBodySpeedTableSize;
    const float t = pos - floorf(pos);
    return mech::kBodySpeedTable[i0] * (1 - t) + mech::kBodySpeedTable[i1] * t;
  }

  void step(float dt) {
    const float w_max = cfg::kMaxCrankRps * 2 * kPi;
    om_l_ += (clampf(duty_l_, -1, 1) * w_max - om_l_) * dt / p_.motor_tau_s;
    om_r_ += (clampf(duty_r_, -1, 1) * w_max - om_r_) * dt / p_.motor_tau_s;
    const float vl = bodySpeed(phi_l_) * om_l_ * p_.travel_scale;
    const float vr = bodySpeed(phi_r_) * om_r_ * p_.travel_scale;
    phi_l_ += om_l_ * dt;
    phi_r_ += om_r_ * dt;
    const float v = 0.5f * (vl + vr);
    const float moving = fminf(1.0f, (fabsf(om_l_) + fabsf(om_r_)) / w_max);
    // 脚が動いているときだけ外乱が入る（ランダムウォーク的なヨーの揺れ）
    yaw_noise_ += (-yaw_noise_ * 5.0f + p_.yaw_disturbance_dps * 30.0f * gauss()) * dt;
    true_yaw_rate_ = (vr - vl) / mech::kLegGroupPitchMm * p_.turn_efficiency +
                     moving * yaw_noise_ * kPi / 180.0f;
    x_ += v * cosf(th_) * dt;
    y_ += v * sinf(th_) * dt;
    th_ += true_yaw_rate_ * dt;
    if (++collision_check_ % 10 == 0 && hitsWall()) ++collisions_;
  }

  // ---- 迷路の幾何（壁厚 12 mm, 柱 12 x 12 mm）----
  int nearbyRects(Rect* out, int max_out) const {
    int n = 0;
    const int cx = cellX(), cy = cellY();
    for (int gx = cx - 2; gx <= cx + 3; ++gx)
      for (int gy = cy - 2; gy <= cy + 3; ++gy) {
        if (gx < 0 || gx > maze::kSize || gy < 0 || gy > maze::kSize) continue;
        if (n < max_out) out[n++] = Rect{180.0f * gx - 6, 180.0f * gy - 6, 180.0f * gx + 6, 180.0f * gy + 6};
        // 区画 (gx, gy) の南壁と西壁（外周は reset 済みの壁として持っている）
        if (gx < maze::kSize && gy <= maze::kSize) {
          const bool south = gy < maze::kSize ? truth_.hasWall(maze::Pos{(int8_t)gx, (int8_t)gy}, maze::kSouth)
                                              : truth_.hasWall(maze::Pos{(int8_t)gx, (int8_t)(gy - 1)}, maze::kNorth);
          if (south && n < max_out) out[n++] = Rect{180.0f * gx + 6, 180.0f * gy - 6, 180.0f * gx + 174, 180.0f * gy + 6};
        }
        if (gy < maze::kSize && gx <= maze::kSize) {
          const bool west = gx < maze::kSize ? truth_.hasWall(maze::Pos{(int8_t)gx, (int8_t)gy}, maze::kWest)
                                             : truth_.hasWall(maze::Pos{(int8_t)(gx - 1), (int8_t)gy}, maze::kEast);
          if (west && n < max_out) out[n++] = Rect{180.0f * gx - 6, 180.0f * gy + 6, 180.0f * gx + 6, 180.0f * gy + 174};
        }
      }
    return n;
  }

  static float rayRect(float ox, float oy, float dx, float dy, const Rect& r) {
    float tmin = 0.0f, tmax = 1e9f;
    const float o[2] = {ox, oy}, d[2] = {dx, dy}, lo[2] = {r.x0, r.y0}, hi[2] = {r.x1, r.y1};
    for (int k = 0; k < 2; ++k) {
      if (fabsf(d[k]) < 1e-9f) {
        if (o[k] < lo[k] || o[k] > hi[k]) return 1e9f;
        continue;
      }
      float t1 = (lo[k] - o[k]) / d[k], t2 = (hi[k] - o[k]) / d[k];
      if (t1 > t2) { const float t = t1; t1 = t2; t2 = t; }
      tmin = fmaxf(tmin, t1);
      tmax = fminf(tmax, t2);
      if (tmin > tmax) return 1e9f;
    }
    return tmin;
  }

  int sense(int idx) {
    const Sensor& s = kSensors[idx];
    const float c = cosf(th_), sn = sinf(th_);
    const float ox = x_ + s.f * c - s.l * sn;
    const float oy = y_ + s.f * sn + s.l * c;
    const float a = th_ + s.angle_deg * kPi / 180.0f;
    Rect rects[160];
    const int n = nearbyRects(rects, 160);
    float d = 1e9f;
    for (int i = 0; i < n; ++i) d = fminf(d, rayRect(ox, oy, cosf(a), sinf(a), rects[i]));
    const float r0 = 30.0f;
    float v = 4000.0f * (r0 / fmaxf(d, 1.0f)) * (r0 / fmaxf(d, 1.0f));
    v = fminf(v, 4000.0f) + p_.sensor_noise * gauss();
    return static_cast<int>(fmaxf(v, 0.0f));
  }

  bool hitsWall() const {
    Rect rects[160];
    const int n = nearbyRects(rects, 160);
    const float c = cosf(th_), sn = sinf(th_);
    for (int k = 0; k < 4; ++k) {  // 外形の 4 辺を 4 mm 間隔で調べる
      const float hl = (k % 2 == 0) ? kHalfLength : kHalfWidth;
      const int steps = static_cast<int>(2 * ((k % 2 == 0) ? kHalfWidth : kHalfLength) / 4.0f);
      for (int i = 0; i <= steps; ++i) {
        const float t = -1.0f + 2.0f * i / steps;
        float f, l;
        if (k == 0) { f = hl; l = t * kHalfWidth; }
        else if (k == 1) { f = t * kHalfLength; l = hl; }
        else if (k == 2) { f = -hl; l = t * kHalfWidth; }
        else { f = t * kHalfLength; l = -hl; }
        const float px = x_ + f * c - l * sn, py = y_ + f * sn + l * c;
        for (int j = 0; j < n; ++j)
          if (px > rects[j].x0 && px < rects[j].x1 && py > rects[j].y0 && py < rects[j].y1) return true;
      }
    }
    return false;
  }

  static float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
  float gauss() {  // 近似正規乱数（一様乱数 4 個の和）
    float s = 0;
    for (int i = 0; i < 4; ++i) {
      rng_ ^= rng_ << 13;
      rng_ ^= rng_ >> 17;
      rng_ ^= rng_ << 5;
      s += (rng_ & 0xFFFF) / 65535.0f;
    }
    return (s - 2.0f) * 1.732f;
  }

  const maze::Maze& truth_;
  SimParams p_;
  uint32_t rng_;
  mouse::Motion* motion_ = nullptr;
  float x_ = 0, y_ = 0, th_ = 0;
  float phi_l_ = 0, phi_r_ = 0, om_l_ = 0, om_r_ = 0;
  float duty_l_ = 0, duty_r_ = 0;
  float true_yaw_rate_ = 0, yaw_noise_ = 0;
  float time_s_ = 0;
  bool sample_front_ = true;
  mouse::WallReading reading_{0, 0, 0, 0};
  int collisions_ = 0;
  uint32_t collision_check_ = 0;
};

constexpr SimRobot::Sensor SimRobot::kSensors[4];

}  // namespace sim
