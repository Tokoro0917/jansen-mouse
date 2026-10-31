// テオヤンセン機構クラシックマウス メインプログラム
//
// MODE ボタンでモード選択（LED 点滅回数 / ブザー音で表示）、START ボタンで実行。
//   0: センサ確認（USB シリアルに壁センサ・ジャイロ・エンコーダ値を出力）
//   1: 探索走行（スタート → ゴール → スタート）
//   2: 最短走行（探索結果の既知壁のみで経路を作り、直線をまとめて走る）
//   3: ストライド較正（5 区画直進。実測距離から cfg::kStrideCorrection を求める）
#include <Arduino.h>

#include "config.h"
#include "hardware.h"
#include "explorer.h"
#include "maze.h"
#include "motion.h"

namespace {

const maze::Pos kGoals[] = {{7, 7}, {7, 8}, {8, 7}, {8, 8}};
const maze::Pos kStart[] = {{0, 0}};
constexpr int kNumModes = 4;

maze::Maze g_maze;
maze::Dir g_heading_after_search = maze::kNorth;
HardwareTimer* g_timer = nullptr;

void controlIsr() { motion.tick(); }

maze::WallObservation senseWalls() {
  const hw::WallReading w = hw::wallSensors();
  return maze::WallObservation{
      w.l > cfg::kWallThrSide,
      (w.fl + w.fr) / 2 > cfg::kWallThrFront,
      w.r > cfg::kWallThrSide,
  };
}

void doTurn(maze::Move mv) {
  switch (mv) {
    case maze::Move::kTurnLeft: motion.turn(90.0f); break;
    case maze::Move::kTurnRight: motion.turn(-90.0f); break;
    case maze::Move::kTurnBack: motion.turn(180.0f); break;
    default: return;
  }
  motion.wait();
}

// 区画中心で停止 → 壁を見る → 旋回 → 1 区画前進 を繰り返す（歩行機構向けの確実な方式）
bool explore(maze::Explorer* ex) {
  while (true) {
    delay(150);  // 歩行振動が収まりセンサ値が落ち着くまで待つ
    const maze::WallObservation seen = senseWalls();
    const maze::Move mv = ex->step(seen);
    if (mv == maze::Move::kArrived) return true;
    if (mv == maze::Move::kStuck) return false;
    if (seen.front && mv != maze::Move::kForward) {
      motion.alignFront();
      motion.wait();
    }
    doTurn(mv);
    ex->applyTurn(mv);
    motion.straight(cfg::kCellMm, cfg::kSearchSpeed, true);
    motion.wait();
    ex->applyForward();
    if (hw::batteryVolts() < cfg::kBatteryCutoffV) return false;
  }
}

void runSearch() {
  g_maze.reset();
  maze::Explorer ex(&g_maze, kGoals, 4);
  if (!explore(&ex)) {
    hw::beep(200, 800);
    return;
  }
  hw::beep(2000, 300);
  ex.setTargets(kStart, 1);
  if (!explore(&ex)) {
    hw::beep(200, 800);
    return;
  }
  g_heading_after_search = ex.heading();
  hw::beep(2500, 150);
  delay(200);
  hw::beep(2500, 150);
}

void runFast() {
  maze::Step steps[128];
  const int n = maze::buildFastPath(g_maze, maze::Pos{0, 0}, maze::kNorth, kGoals, 4, steps, 128);
  if (n < 0) {
    hw::beep(200, 800);  // 未探索、または経路なし
    return;
  }
  for (int i = 0; i < n; ++i) {
    switch (steps[i].action) {
      case maze::Action::kStraight:
        motion.straight(cfg::kCellMm * steps[i].cells, cfg::kFastSpeed, true);
        motion.wait();
        break;
      case maze::Action::kTurnLeft: doTurn(maze::Move::kTurnLeft); break;
      case maze::Action::kTurnRight: doTurn(maze::Move::kTurnRight); break;
      case maze::Action::kTurnBack: doTurn(maze::Move::kTurnBack); break;
    }
  }
  hw::beep(3000, 500);
}

void runStrideCalibration() {
  const float start = motion.distanceMm();
  motion.straight(cfg::kCellMm * 5, cfg::kSearchSpeed, false);
  motion.wait();
  Serial.printf("odometry: %.1f mm (target %.1f mm)\n", motion.distanceMm() - start,
                cfg::kCellMm * 5);
  Serial.println("実測距離 / 900 を cfg::kStrideCorrection に掛けてください");
}

void runSensorMonitor() {
  while (!hw::modeButton()) {
    const hw::WallReading w = hw::wallSensors();
    Serial.printf("FL %4d  L %4d  R %4d  FR %4d | yaw %7.1f | encL %7ld encR %7ld | %.2f V\n",
                  w.fl, w.l, w.r, w.fr, motion.yawDeg(), (long)hw::encoderLeft(),
                  (long)hw::encoderRight(), hw::batteryVolts());
    delay(100);
  }
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
  motion.begin();

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
    case 1: runSearch(); break;
    case 2: runFast(); break;
    case 3: runStrideCalibration(); break;
  }
  motion.stop();
}
