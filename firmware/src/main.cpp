// テオヤンセン機構クラシックマウス メインプログラム
//
// MODE ボタンでモード選択（LED 点滅回数 / ブザー音で表示）、START ボタンで実行。
//   0: センサ確認（USB シリアルに壁センサ・ジャイロ・エンコーダ値を出力）
//   1: 探索走行（スタート → ゴール → スタート）
//   2: 最短走行（探索結果の既知壁のみで経路を作り、直線をまとめて走る）
//   3: 前進量の較正（5 区画直進。実測距離から cfg::kTravelCorrection を求める）
//
// 走行制御（lib/mouse/motion）と探索手順（lib/mouse/runner）はハードウェア非依存で、
// PC 上のシミュレーション（test/test_sim）でも同じコードが動く。
#include <Arduino.h>

#include "config.h"
#include "hardware.h"
#include "motion.h"
#include "runner.h"

namespace {

constexpr int kNumModes = 4;

hw::HardwareIO g_io;
mouse::WallTuning g_tuning;  // 実機で計測した値に書き換える（docs/hardware.md 参照）
mouse::Motion g_motion(g_io, g_tuning);
mouse::Runner g_runner(g_io, g_motion, g_tuning);
HardwareTimer* g_timer = nullptr;

void controlIsr() { g_motion.tick(); }

void beepResult(mouse::RunResult r) {
  if (r == mouse::RunResult::kOk) {
    hw::beep(2500, 150);
    delay(200);
    hw::beep(2500, 150);
  } else {
    hw::beep(200, 800);
  }
}

void runSensorMonitor() {
  while (!hw::modeButton()) {
    const hw::WallReading w = hw::wallSensors();
    Serial.printf("FL %4d  L %4d  R %4d  FR %4d | yaw %7.1f | encL %7ld encR %7ld | %.2f V\n",
                  w.fl, w.l, w.r, w.fr, g_motion.yawDeg(), (long)hw::encoderLeft(),
                  (long)hw::encoderRight(), hw::batteryVolts());
    delay(100);
  }
}

void runTravelCalibration() {
  const float odo = g_runner.walkCells(5);
  Serial.printf("odometry: %.1f mm (target %.1f mm)\n", odo, cfg::kCellMm * 5);
  Serial.println("実測距離 / 900 を cfg::kTravelCorrection に掛けてください");
}

int selectMode() {
  int mode = 0;
  while (true) {
    if (hw::modeButton()) {
      mode = (mode + 1) % kNumModes;
      hw::beep(1000 + 300 * mode, 60);
      while (hw::modeButton()) delay(10);
    }
    if (hw::startButton()) {
      while (hw::startButton()) delay(10);
      return mode;
    }
    // モード番号 + 1 回だけ LED を点滅させる
    const uint32_t t = millis() % 2000;
    hw::led(t < (uint32_t)(mode + 1) * 200 && (t / 100) % 2 == 0);
    delay(10);
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  hw::uiBegin();
  hw::motorsBegin();
  hw::encodersBegin();
  hw::wallSensorsBegin();
  if (!hw::imuBegin()) {
    while (true) {  // IMU なしでは走行できない
      hw::beep(200, 100);
      delay(500);
    }
  }
  hw::imuCalibrate(1000);  // 静止状態で 1 秒間ジャイロのバイアスを測る
  g_motion.begin();

  g_timer = new HardwareTimer(TIM11);  // TIM10 は tone() が使用
  g_timer->setOverflow(static_cast<uint32_t>(cfg::kControlHz), HERTZ_FORMAT);
  g_timer->attachInterrupt(controlIsr);
  g_timer->resume();
  hw::beep(1500, 100);
}

void loop() {
  const int mode = selectMode();
  delay(1000);  // 手を離す時間
  switch (mode) {
    case 0: runSensorMonitor(); break;
    case 1: beepResult(g_runner.search([] { hw::beep(2000, 300); })); break;
    case 2: beepResult(g_runner.fastRun()); break;
    case 3: runTravelCalibration(); break;
  }
  g_motion.stop();
}
