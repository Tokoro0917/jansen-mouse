#include "motion.h"

#include <math.h>

#include "config.h"

namespace mouse {

namespace {
constexpr float kDegToRad = 3.14159265f / 180.0f;
constexpr int kAlignTicks = 400;    // 前壁補正の実行時間 [tick]
constexpr int kTurnTimeoutTicks = 500;  // 旋回の目標角に収束するまでの猶予 [tick]
constexpr float kTurnDoneDeg = 0.5f;    // 旋回完了とみなす角度誤差 [deg]
constexpr float kTurnDoneRateDps = 5.0f;  // 旋回完了とみなす角速度 [deg/s]
constexpr float kStraightDoneMm = 1.0f;   // 直進完了とみなす距離誤差 [mm]
constexpr int kStraightTimeoutTicks = 500;
constexpr float kWallTrimLimitDeg = 10.0f;
constexpr float kLowPass = 0.05f;   // 速度・センサのローパス係数（歩行振動対策）
constexpr float kEdgeLowPass = 0.3f;  // 壁切れ検出用のローパス係数（遅れ数 ms）
constexpr float kEdgeOnRatio = 1.3f;  // 壁あり判定のヒステリシス（閾値に対する比）
constexpr float kEdgeOffRatio = 0.7f;
constexpr float kEdgeMaxCorrectionMm = 25.0f;  // これ以上ずれた壁切れは別の柱とみなして無視
// 中央寄せに使うのは、この距離以上続けて見えている横壁だけ（柱 12 mm の一瞬の反射を壁と誤らない）
constexpr float kWallMinRunMm = 25.0f;
// 横壁が切れる位置: 区画中心から (半区画 + 柱の半分) 先が柱の向こう端。
// センサはクランク軸より前にあるので、そのとき機体中心は区画中心からこの距離だけ進んでいる。
constexpr float kWallEdgeMm = cfg::kCellMm / 2 + cfg::kPostHalfMm - cfg::kSideSensorForwardMm;

float clamp(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

// 赤外センサの値は距離のほぼ 2 乗に反比例する。区画中央での値 ref（そのときの距離 ref_dist）を基準に、
// いまの値から距離 [mm] を求める。こうしておくと、センサの取り付け位置や感度が変わっても制御のゲインが変わらない。
float wallDistance(float value, float ref, float ref_dist) {
  return ref_dist * sqrtf(ref / (value > 1.0f ? value : 1.0f));
}
}  // namespace

void Motion::begin() {
  pid_l_ = control::Pid(cfg::kCrankKp, cfg::kCrankKi, cfg::kCrankKd, 1.0f);
  pid_r_ = control::Pid(cfg::kCrankKp, cfg::kCrankKi, cfg::kCrankKd, 1.0f);
  prev_enc_l_ = io_.encoderLeft();
  prev_enc_r_ = io_.encoderRight();
}

float Motion::distanceMm() const {
  const float revs = 0.5f * (io_.encoderLeft() + io_.encoderRight()) / cfg::kCountsPerCrankRev;
  return revs * cfg::kMmPerCrankRev;
}

void Motion::straight(float mm, float v_max, bool wall_centering) {
  io_.lock();
  profile_.start(mm, v_max, cfg::kAccel);
  wall_centering_ = wall_centering;
  straight_start_mm_ = distanceMm();
  wall_seen_l_ = edge_l_ > tuning_.thr_side;
  wall_seen_r_ = edge_r_ > tuning_.thr_side;
  seen_since_l_ = seen_since_r_ = -cfg::kCellMm;  // 開始時から見えている壁は区画の壁
  settle_ticks_ = kStraightTimeoutTicks;
  mode_ = Mode::kStraight;
  io_.unlock();
}

void Motion::turn(float deg) {
  io_.lock();
  profile_.start(deg, cfg::kTurnRate, cfg::kTurnAccel);
  turn_start_ = heading_ref_ + wall_trim_;
  turn_goal_ = turn_start_ + deg;
  heading_ref_ += deg;
  settle_ticks_ = kTurnTimeoutTicks;
  mode_ = Mode::kTurn;
  io_.unlock();
}

void Motion::alignFront() {
  io_.lock();
  settle_ticks_ = kAlignTicks;
  mode_ = Mode::kAlign;
  io_.unlock();
}

void Motion::stop() {
  io_.lock();
  stopLocked();
  io_.unlock();
}

void Motion::stopLocked() {
  mode_ = Mode::kIdle;
  pid_l_.reset();
  pid_r_.reset();
  io_.motorsBrake();
}

void Motion::wait() {
  while (busy()) io_.delayMs(1);
}

void Motion::drive(float v_mm_s, float w_deg_s) {
  const float half = 0.5f * cfg::kEffectiveTreadMm * w_deg_s * kDegToRad;
  const float ref_l = (v_mm_s - half) / cfg::kMmPerCrankRev;  // [rev/s]
  const float ref_r = (v_mm_s + half) / cfg::kMmPerCrankRev;
  const float ff_l = ref_l / cfg::kMaxCrankRps;
  const float ff_r = ref_r / cfg::kMaxCrankRps;
  io_.motorsSet(ff_l + pid_l_.update(ref_l - rps_l_, cfg::kDt),
                ff_r + pid_r_.update(ref_r - rps_r_, cfg::kDt));
}

// 壁切れ（横壁がなくなる瞬間）で走行距離を補正する。
// 直進は必ず区画中心から始まるので、壁切れが起きる走行距離は k x 区画 + kWallEdgeMm に決まる。
void Motion::detectWallEdge(float value, bool* seen, float* seen_since_mm, float traveled_mm) {
  if (!*seen) {
    if (value > tuning_.thr_side * kEdgeOnRatio) {
      *seen = true;
      *seen_since_mm = traveled_mm;
    }
    return;
  }
  if (value >= tuning_.thr_side * kEdgeOffRatio) return;
  *seen = false;
  const float k = static_cast<float>(static_cast<int>((traveled_mm - kWallEdgeMm) / cfg::kCellMm + 0.5f));
  if (k < 0) return;
  const float offset = (k * cfg::kCellMm + kWallEdgeMm) - traveled_mm;
  if (offset > kEdgeMaxCorrectionMm || offset < -kEdgeMaxCorrectionMm) return;
  straight_start_mm_ -= offset;  // 走行距離を壁切れの位置に合わせる
  ++edge_corrections_;
}

void Motion::tick() {
  // ---- センサ更新 ----
  const int32_t el = io_.encoderLeft();
  const int32_t er = io_.encoderRight();
  const float inst_l = (el - prev_enc_l_) / cfg::kCountsPerCrankRev * cfg::kControlHz;
  const float inst_r = (er - prev_enc_r_) / cfg::kCountsPerCrankRev * cfg::kControlHz;
  prev_enc_l_ = el;
  prev_enc_r_ = er;
  rps_l_ += kLowPass * (inst_l - rps_l_);
  rps_r_ += kLowPass * (inst_r - rps_r_);

  const float yaw_rate = io_.yawRateDps();
  yaw_ += yaw_rate * cfg::kDt;

  io_.wallSensorsSample();
  const WallReading w = io_.wallSensors();
  sens_l_ += kLowPass * (w.l - sens_l_);
  sens_r_ += kLowPass * (w.r - sens_r_);
  edge_l_ += kEdgeLowPass * (w.l - edge_l_);
  edge_r_ += kEdgeLowPass * (w.r - edge_r_);

  // ---- 動作ごとの指令生成 ----
  switch (mode_) {
    case Mode::kIdle:
      return;

    case Mode::kStraight: {
      // 速度プロファイル + エンコーダ距離のフィードバック（速度追従の遅れを距離誤差として残さない）
      const float v_ref = profile_.update(cfg::kDt);
      if (wall_centering_) {
        detectWallEdge(edge_l_, &wall_seen_l_, &seen_since_l_, distanceMm() - straight_start_mm_);
        detectWallEdge(edge_r_, &wall_seen_r_, &seen_since_r_, distanceMm() - straight_start_mm_);
      }
      const float dist_err = profile_.position() - (distanceMm() - straight_start_mm_);
      const float v = v_ref + cfg::kDistanceKp * dist_err;
      float w_cmd = cfg::kHeadingKp * (heading_ref_ + wall_trim_ - yaw_);
      if (wall_centering_) {
        const float traveled = distanceMm() - straight_start_mm_;
        const bool wl = wall_seen_l_ && traveled - seen_since_l_ > kWallMinRunMm;
        const bool wr = wall_seen_r_ && traveled - seen_since_r_ > kWallMinRunMm;
        // 区画中央からの横ずれ [mm]（正: 左壁に近い）
        const float off_l = cfg::kSideWallDistMm - wallDistance(sens_l_, tuning_.side_ref_l, cfg::kSideWallDistMm);
        const float off_r = cfg::kSideWallDistMm - wallDistance(sens_r_, tuning_.side_ref_r, cfg::kSideWallDistMm);
        float err = 0.0f;
        if (wl && wr) err = 0.5f * (off_l - off_r);
        else if (wl) err = off_l;
        else if (wr) err = -off_r;
        w_cmd -= cfg::kWallCenterKp * err;
        // 壁から見てずれ続けるなら、ジャイロの向きの基準自体を少しずつ直す（積分動作）
        wall_trim_ = clamp(wall_trim_ - cfg::kWallTrimGain * err * cfg::kDt,
                           -kWallTrimLimitDeg, kWallTrimLimitDeg);
      }
      drive(v, w_cmd);
      // 前壁に区画中心の距離まで近づいたら、走行距離の推定が足りなくてもそこで止まる
      // （両側に壁が続く通路では壁切れがなく、前進量の誤差がたまるため）
      if (wall_centering_ && w.fl + w.fr >= tuning_.front_ref_sum) {
        stopLocked();
        return;
      }
      if (profile_.done() &&
          ((dist_err < kStraightDoneMm && dist_err > -kStraightDoneMm) || --settle_ticks_ <= 0)) {
        stopLocked();
      }
      return;
    }

    case Mode::kTurn: {
      const float w_ref = profile_.update(cfg::kDt);
      const float angle_ref = turn_start_ + profile_.position();
      drive(0.0f, w_ref + cfg::kYawRateKp * (w_ref - yaw_rate) +
                      cfg::kTurnAngleKp * (angle_ref - yaw_));
      // 指令プロファイルが終わり、目標角に収束したら完了（収束しなくても猶予で打ち切る）
      if (profile_.done()) {
        const float err = turn_goal_ - yaw_;
        if ((err < kTurnDoneDeg && err > -kTurnDoneDeg && yaw_rate < kTurnDoneRateDps &&
             yaw_rate > -kTurnDoneRateDps) ||
            --settle_ticks_ <= 0) {
          stopLocked();
        }
      }
      return;
    }

    case Mode::kAlign: {
      // 前壁までの距離（FL+FR）と傾き（FL-FR）を目標値に寄せる。
      // 時計回りに傾くと左前センサが壁に近づき FL > FR になるので、反時計回り（正）に回す。
      const float ref = 0.5f * tuning_.front_ref_sum;
      const float d_fl = wallDistance(static_cast<float>(w.fl), ref, cfg::kFrontWallDistMm);
      const float d_fr = wallDistance(static_cast<float>(w.fr), ref, cfg::kFrontWallDistMm);
      const float dist_err = 0.5f * (d_fl + d_fr) - cfg::kFrontWallDistMm;  // 正: 遠い → 前進
      const float ang_err = atan2f(d_fr - d_fl, cfg::kFrontSensorSpanMm) / kDegToRad;  // 正: 反時計回りに回す
      drive(clamp(cfg::kAlignDistKp * dist_err, -30.0f, 30.0f),
            clamp(cfg::kAlignAngleKp * ang_err, -60.0f, 60.0f));
      if (--settle_ticks_ <= 0) {
        // 前壁と直角になった = 迷路に対して理想の向き。ジャイロの累積誤差をここで消す。
        yaw_ = heading_ref_;
        wall_trim_ = 0.0f;
        stopLocked();
      }
      return;
    }
  }

}

}  // namespace mouse
