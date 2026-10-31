#include "motion.h"

#include <Arduino.h>

#include "config.h"
#include "hardware.h"

Motion motion;

namespace {
constexpr float kDegToRad = 3.14159265f / 180.0f;
constexpr int kSettleTicks = 100;   // 動作終了後の静定時間 [tick]
constexpr int kAlignTicks = 400;    // 前壁補正の実行時間 [tick]
constexpr float kLowPass = 0.05f;   // 速度・センサのローパス係数（歩行振動対策）
}  // namespace

void Motion::begin() {
  pid_l_ = control::Pid(cfg::kCrankKp, cfg::kCrankKi, cfg::kCrankKd, 1.0f);
  pid_r_ = control::Pid(cfg::kCrankKp, cfg::kCrankKi, cfg::kCrankKd, 1.0f);
  prev_enc_l_ = hw::encoderLeft();
  prev_enc_r_ = hw::encoderRight();
}

float Motion::distanceMm() const {
  const float revs = 0.5f * (hw::encoderLeft() + hw::encoderRight()) / cfg::kCountsPerCrankRev;
  return revs * cfg::kMmPerCrankRev;
}

void Motion::straight(float mm, float v_max, bool wall_centering) {
  noInterrupts();
  profile_.start(mm, v_max, cfg::kAccel);
  wall_centering_ = wall_centering;
  settle_ticks_ = kSettleTicks;
  mode_ = Mode::kStraight;
  interrupts();
}

void Motion::turn(float deg) {
  noInterrupts();
  profile_.start(deg, cfg::kTurnRate, cfg::kTurnAccel);
  turn_start_yaw_ = target_yaw_;
  target_yaw_ += deg;
  settle_ticks_ = kSettleTicks;
  mode_ = Mode::kTurn;
  interrupts();
}

void Motion::alignFront() {
  noInterrupts();
  settle_ticks_ = kAlignTicks;
  mode_ = Mode::kAlign;
  interrupts();
}

void Motion::stop() {
  noInterrupts();
  mode_ = Mode::kIdle;
  pid_l_.reset();
  pid_r_.reset();
  hw::motorsBrake();
  interrupts();
}

void Motion::wait() const {
  while (busy()) delay(1);
}

void Motion::drive(float v_mm_s, float w_deg_s) {
  const float half = 0.5f * cfg::kEffectiveTreadMm * w_deg_s * kDegToRad;
  const float ref_l = (v_mm_s - half) / cfg::kMmPerCrankRev;  // [rev/s]
  const float ref_r = (v_mm_s + half) / cfg::kMmPerCrankRev;
  const float ff_l = ref_l / cfg::kMaxCrankRps;
  const float ff_r = ref_r / cfg::kMaxCrankRps;
  hw::motorsSet(ff_l + pid_l_.update(ref_l - rps_l_, cfg::kDt),
                ff_r + pid_r_.update(ref_r - rps_r_, cfg::kDt));
}

void Motion::tick() {
  // ---- センサ更新 ----
  const int32_t el = hw::encoderLeft();
  const int32_t er = hw::encoderRight();
  const float inst_l = (el - prev_enc_l_) / cfg::kCountsPerCrankRev * cfg::kControlHz;
  const float inst_r = (er - prev_enc_r_) / cfg::kCountsPerCrankRev * cfg::kControlHz;
  prev_enc_l_ = el;
  prev_enc_r_ = er;
  rps_l_ += kLowPass * (inst_l - rps_l_);
  rps_r_ += kLowPass * (inst_r - rps_r_);

  const float yaw_rate = hw::imuYawRateDps();
  yaw_ += yaw_rate * cfg::kDt;

  hw::wallSensorsSample();
  const hw::WallReading w = hw::wallSensors();
  sens_l_ += kLowPass * (w.l - sens_l_);
  sens_r_ += kLowPass * (w.r - sens_r_);

  // ---- 動作ごとの指令生成 ----
  switch (mode_) {
    case Mode::kIdle:
      return;

    case Mode::kStraight: {
      const float v = profile_.update(cfg::kDt);
      float w_cmd = cfg::kHeadingKp * (target_yaw_ - yaw_);
      if (wall_centering_) {
        const bool wl = sens_l_ > cfg::kWallThrSide;
        const bool wr = sens_r_ > cfg::kWallThrSide;
        float err = 0.0f;  // 正: 左壁に近い
        if (wl && wr) err = (sens_l_ - cfg::kSideRefL) - (sens_r_ - cfg::kSideRefR);
        else if (wl) err = 2.0f * (sens_l_ - cfg::kSideRefL);
        else if (wr) err = -2.0f * (sens_r_ - cfg::kSideRefR);
        w_cmd -= cfg::kWallCenterKp * err;
      }
      drive(v, w_cmd);
      break;
    }

    case Mode::kTurn: {
      const float w_ref = profile_.update(cfg::kDt);
      const float angle_ref = turn_start_yaw_ + profile_.position();
      drive(0.0f, w_ref + cfg::kYawRateKp * (w_ref - yaw_rate) +
                      cfg::kHeadingKp * (angle_ref - yaw_));
      break;
    }

    case Mode::kAlign: {
      // 前壁までの距離（FL+FR）と傾き（FL-FR）を目標値に寄せる
      const float dist_err = (cfg::kFrontRefSum - (w.fl + w.fr)) * 0.02f;  // [mm/s]
      const float ang_err = (w.fr - w.fl) * 0.05f;                         // [deg/s]
      drive(constrain(dist_err, -30.0f, 30.0f), constrain(ang_err, -60.0f, 60.0f));
      if (--settle_ticks_ <= 0) {
        target_yaw_ = yaw_;  // 前壁で揃えた向きを新しい基準にする
        stop();
      }
      return;
    }
  }

  if (profile_.done() && --settle_ticks_ <= 0) stop();
}
