// 機構・制御の調整パラメータ（ハードウェア非依存。ピン割り当ては src/pins.h）
#pragma once

#include <stdint.h>

#include "mechanism_params.h"

namespace cfg {

// ---------------- 機構 ----------------
constexpr float kCellMm = 180.0f;
constexpr float kPostHalfMm = 6.0f;           // 柱（12 mm 角）の半分
// 左右の壁センサ: 基板の前端より内側から斜め前（mech::kSideSensorAngleDeg）に向け、横の壁を見る（mechanism/jansen/body.py）。
// kSideLookAheadMm: 区画中央にいるとき、光が横の壁に当たる点の機体中心からの前方距離 [mm]。壁切れ・横壁の読み取りはこの点で考える。
constexpr float kSideLookAheadMm = mech::kSideLookAheadMm;
// 区画中央にいるときの、各センサから壁面までの光の長さ [mm]（壁面は区画中心から 84 mm）
constexpr float kSideWallDistMm = mech::kSideBeamToWallMm;
// 光の長さの変化 → 横ずれ への換算（横に δ ずれると光の長さは δ / sin(向き) 変わる）
constexpr float kSideBeamSin = mech::kSideSensorSin;
constexpr float kFrontWallDistMm = 84.0f - mech::kFrontSensorForwardMm;
constexpr float kFrontSensorSpanMm = 2.0f * mech::kFrontSensorLateralMm;  // FL と FR の左右間隔
constexpr float kEncoderCountsPerMotorRev = 28.0f;  // 7 極対 x 4 逓倍
constexpr float kGearRatio = 100.0f;                // ギヤ比（購入したモータに合わせる）
constexpr float kCountsPerCrankRev = kEncoderCountsPerMotorRev * kGearRatio;
// 片側の左右モータ取り付け向き補正（前進でカウントが増えるように）
constexpr int kMotorLSign = 1;
constexpr int kMotorRSign = -1;
// 超信地旋回の実効トレッド [mm]（初期値は左右脚群の中心間距離。旋回はジャイロで閉ループ）
constexpr float kEffectiveTreadMm = mech::kLegGroupPitchMm;
// 1 回転あたり前進量の補正係数（モード 3 で実測距離 / 理論距離 から調整）。
// 理論値は脚の滑りをモデル化した近似なので、実機では数 % ずれる。
constexpr float kTravelCorrection = 1.00f;
constexpr float kMmPerCrankRev = mech::kTravelMmPerRev * kTravelCorrection;

// ---------------- 制御 ----------------
constexpr float kControlHz = 1000.0f;
constexpr float kDt = 1.0f / kControlHz;

constexpr float kSearchSpeed = 90.0f;    // [mm/s] 探索 (≈1.6 rev/s)。速度ごとの比較は docs/design.md
constexpr float kFastSpeed = 90.0f;      // [mm/s] 最短走行 (≈1.6 rev/s)
constexpr float kAccel = 150.0f;         // [mm/s^2]
constexpr float kTurnRate = 180.0f;      // [deg/s]
constexpr float kTurnAccel = 540.0f;     // [deg/s^2]

constexpr float kMaxCrankRps = 2.5f;  // duty 1.0 でのクランク回転数（150 rpm 品。フィードフォワード用）
// クランク回転速度 PID (誤差 rev/s -> PWM duty [-1, 1])
constexpr float kCrankKp = 0.6f, kCrankKi = 6.0f, kCrankKd = 0.0f;
// 直進時の距離フィードバック (誤差 mm -> 速度補正 mm/s)
constexpr float kDistanceKp = 4.0f;
// 直進時の向き保持 (誤差 deg -> 角速度補正 deg/s)
constexpr float kHeadingKp = 4.0f;
// 左右壁による中央寄せ (横ずれ mm -> 角速度補正 deg/s)
constexpr float kWallCenterKp = 1.0f;
// 中央寄せの積分: 壁から見たずれを向きの基準に反映する速さ (横ずれ mm -> deg/s)
constexpr float kWallTrimGain = 0.2f;
// 前壁補正 (距離誤差 mm -> 速度 mm/s, 傾き deg -> 角速度 deg/s)
constexpr float kAlignDistKp = 3.0f;
constexpr float kAlignAngleKp = 8.0f;
// 旋回時の角速度追従 (誤差 deg/s -> 角速度補正 deg/s)
constexpr float kYawRateKp = 1.5f;
// 旋回時の角度追従 (誤差 deg -> 角速度補正 deg/s)。足の横滑りで実効が落ちるので直進より強くする
constexpr float kTurnAngleKp = 15.0f;

constexpr float kBatteryCutoffV = 6.6f;  // 2S LiPo 下限

}  // namespace cfg
