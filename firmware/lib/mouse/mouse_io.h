// 走行制御・探索から見たハードウェアの窓口。
// 実機は src/hardware.cpp、PC 上のシミュレーションは test/test_sim/sim_robot.h が実装する。
#pragma once

#include <stdint.h>

namespace mouse {

struct WallReading {
  int fl, l, r, fr;  // 点灯時 - 消灯時（12bit ADC）
};

class MouseIO {
 public:
  virtual ~MouseIO() = default;

  // モータ（duty: -1.0〜1.0、前進が正）
  virtual void motorsSet(float left, float right) = 0;
  virtual void motorsBrake() = 0;

  // エンコーダ（前進でカウントが増える向きに補正済み）
  virtual int32_t encoderLeft() const = 0;
  virtual int32_t encoderRight() const = 0;

  // 壁センサ: sample() を制御周期ごとに呼び、read() で最新値を得る
  virtual void wallSensorsSample() = 0;
  virtual WallReading wallSensors() const = 0;

  // ジャイロ: ヨー角速度 [deg/s]（反時計回りが正、バイアス除去済み）
  virtual float yawRateDps() = 0;

  virtual float batteryVolts() const = 0;

  // メインループ側の待ち。実機は delay()、シミュレーションは時間を進める。
  virtual void delayMs(int ms) = 0;

  // 制御割り込みとの排他（実機は割り込み禁止、シミュレーションは何もしない）
  virtual void lock() = 0;
  virtual void unlock() = 0;
};

}  // namespace mouse
