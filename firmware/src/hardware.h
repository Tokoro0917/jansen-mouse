// 実機ドライバ群
#pragma once

#include <Arduino.h>

#include "mouse_io.h"

namespace hw {

using mouse::WallReading;

// ---- モータ ----
void motorsBegin();
// duty: -1.0 〜 1.0（前進が正）
void motorsSet(float left, float right);
void motorsBrake();

// ---- エンコーダ（クランク軸換算） ----
void encodersBegin();
int32_t encoderLeft();
int32_t encoderRight();

// ---- 壁センサ ----
void wallSensorsBegin();
// 制御周期ごとに呼ぶ（前方/側方を交互にサンプリングする）
void wallSensorsSample();
WallReading wallSensors();

// ---- IMU（ヨー角速度）----
bool imuBegin();
void imuCalibrate(int samples);
float imuYawRateDps();  // 反時計回りが正

// ---- UI ----
void uiBegin();
void beep(int freq_hz, int ms);
void led(bool on);
bool modeButton();
bool startButton();
float batteryVolts();

// 走行制御・探索から使う窓口（mouse::MouseIO の実機実装）
class HardwareIO : public mouse::MouseIO {
 public:
  void motorsSet(float left, float right) override { hw::motorsSet(left, right); }
  void motorsBrake() override { hw::motorsBrake(); }
  int32_t encoderLeft() const override { return hw::encoderLeft(); }
  int32_t encoderRight() const override { return hw::encoderRight(); }
  void wallSensorsSample() override { hw::wallSensorsSample(); }
  WallReading wallSensors() const override { return hw::wallSensors(); }
  float yawRateDps() override { return hw::imuYawRateDps(); }
  float batteryVolts() const override { return hw::batteryVolts(); }
  void delayMs(int ms) override { delay(ms); }
  void lock() override { noInterrupts(); }
  void unlock() override { interrupts(); }
};

}  // namespace hw
