// ピン割り当て (WeAct Black Pill STM32F411CEU6)
#pragma once

#include <Arduino.h>

namespace pins {

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

}  // namespace pins
