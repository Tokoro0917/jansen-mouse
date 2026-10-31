// ハードウェア構成・調整パラメータ
#pragma once

#include <stdint.h>

#include "mechanism_params.h"

namespace cfg {

// ---------------- ピン割り当て (WeAct Black Pill STM32F411CEU6) ----------------
// モータドライバ DRV8835 (MODE=High: PHASE/ENABLE モード)
constexpr uint32_t kPinMotorLPwm = PA8;    // AENBL  (TIM1_CH1)
constexpr uint32_t kPinMotorLDir = PB12;   // APHASE
constexpr uint32_t kPinMotorRPwm = PA9;    // BENBL  (TIM1_CH2)
constexpr uint32_t kPinMotorRDir = PB13;   // BPHASE

// モータ軸の磁気エンコーダ (A/B 相)
constexpr uint32_t kPinEncLA = PB4;
constexpr uint32_t kPinEncLB = PB5;
constexpr uint32_t kPinEncRA = PB6;
constexpr uint32_t kPinEncRB = PB7;

// 壁センサ: 赤外 LED (MOSFET 駆動) とフォトトランジスタ (ADC)
constexpr uint32_t kPinIrLedFront = PB14;  // 前方 2 個を同時点灯
constexpr uint32_t kPinIrLedSide = PB15;   // 左右 2 個を同時点灯
constexpr uint32_t kPinSensFL = PA0;
constexpr uint32_t kPinSensL = PA1;
constexpr uint32_t kPinSensR = PA2;
constexpr uint32_t kPinSensFR = PA3;

// IMU (ICM-20602 / MPU-6500 互換, SPI1)
constexpr uint32_t kPinImuCs = PA4;        // SCK=PA5, MISO=PA6, MOSI=PA7

// その他
constexpr uint32_t kPinBattery = PB1;      // 分圧 1/3 (20k + 10k)
constexpr uint32_t kPinBuzzer = PA15;
constexpr uint32_t kPinLed = PC13;         // オンボード LED (Low で点灯)
constexpr uint32_t kPinBtnMode = PA10;     // 内部プルアップ, 押下で Low
constexpr uint32_t kPinBtnStart = PB3;

// ---------------- 機構 ----------------
constexpr float kCellMm = 180.0f;
constexpr float kEncoderCountsPerMotorRev = 28.0f;  // 7 極対 x 4 逓倍
constexpr float kGearRatio = 100.0f;                // N20 ウォームギヤモータの減速比（購入品に合わせる）
constexpr float kCountsPerCrankRev = kEncoderCountsPerMotorRev * kGearRatio;
// 片側の左右モータ取り付け向き補正（前進でカウントが増えるように）
constexpr int kMotorLSign = 1;
constexpr int kMotorRSign = -1;
// 超信地旋回の実効トレッド [mm]（初期値は左右脚群の中心間距離。旋回はジャイロで閉ループ）
constexpr float kEffectiveTreadMm = mech::kLegGroupPitchMm;
// 歩行の実効ストライド補正係数（実測距離 / 理論距離 から調整）
constexpr float kStrideCorrection = 1.00f;
constexpr float kMmPerCrankRev = mech::kStrideMmPerRev * kStrideCorrection;

// ---------------- 制御 ----------------
constexpr float kControlHz = 1000.0f;
constexpr float kDt = 1.0f / kControlHz;

constexpr float kSearchSpeed = 60.0f;    // [mm/s] 探索 (≈2.5 rev/s)
constexpr float kFastSpeed = 90.0f;      // [mm/s] 最短走行 (≈3.8 rev/s)
constexpr float kAccel = 150.0f;         // [mm/s^2]
constexpr float kTurnRate = 180.0f;      // [deg/s]
constexpr float kTurnAccel = 540.0f;     // [deg/s^2]

constexpr float kMaxCrankRps = 5.5f;  // duty 1.0 での無負荷クランク回転数（フィードフォワード用）
// クランク回転速度 PID (誤差 rev/s -> PWM duty [-1, 1])
constexpr float kCrankKp = 0.6f, kCrankKi = 6.0f, kCrankKd = 0.0f;
// 直進時の向き保持 (誤差 deg -> 角速度補正 deg/s)
constexpr float kHeadingKp = 4.0f;
// 左右壁による中央寄せ (センサ差 -> 角速度補正 deg/s)
constexpr float kWallCenterKp = 0.02f;
// 旋回時の角速度追従 (誤差 deg/s -> 角速度補正 deg/s)
constexpr float kYawRateKp = 1.5f;

// ---------------- 壁センサ閾値（ADC 12bit, 点灯 - 消灯 の差分）----------------
constexpr int kWallThrFront = 180;
constexpr int kWallThrSide = 220;
constexpr int kSideRefL = 900;   // 区画中央にいるときの左右センサ値（実機で計測して設定）
constexpr int kSideRefR = 900;
constexpr int kFrontRefSum = 2600;  // 前壁があるとき中央で停止している際の FL+FR

constexpr float kBatteryCutoffV = 6.6f;  // 2S LiPo 下限

}  // namespace cfg
