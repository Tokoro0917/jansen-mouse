// 実機ドライバ群
#pragma once

#include <Arduino.h>

namespace hw {

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
struct WallReading {
  int fl, l, r, fr;  // 点灯時 - 消灯時
};
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

}  // namespace hw
