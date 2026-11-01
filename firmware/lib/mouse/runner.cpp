#include "runner.h"

#include "config.h"

namespace mouse {

constexpr maze::Pos Runner::kGoals[4];
constexpr maze::Pos Runner::kStart[1];

maze::WallObservation Runner::senseWalls() const {
  const WallReading w = io_.wallSensors();
  return maze::WallObservation{
      w.l > tuning_.thr_side,
      (w.fl + w.fr) / 2 > tuning_.thr_front,
      w.r > tuning_.thr_side,
  };
}

void Runner::doTurn(maze::Move mv) {
  switch (mv) {
    case maze::Move::kTurnLeft: motion_.turn(90.0f); break;
    case maze::Move::kTurnRight: motion_.turn(-90.0f); break;
    case maze::Move::kTurnBack: motion_.turn(180.0f); break;
    default: return;
  }
  motion_.wait();
}

// 区画中心で停止 → 壁を見る → 旋回 → 1 区画前進 を繰り返す（歩行機構向けの確実な方式）
namespace {
// 横壁は、左右センサの光が次の区画の横壁の真ん中に当たる瞬間（機体中心が区画中心の kSideLookAheadMm 手前）に読む。
// 光は機体中心より前の壁に当たるので、区画中心で止まってから読むと、前後に行き過ぎたときに
// 次の区画の壁を見てしまう（余裕は 84 - kSideLookAheadMm）。通過時に読めば、前後の誤差に ±78 mm まで耐える。
constexpr int kSideSampleTicks = 10;  // この tick 数の平均をとる（約 1 mm の区間）
}  // namespace

// 1 区画前進し、途中で次の区画の横壁を読む。読めたら true。
bool Runner::forwardOneCell(bool* left, bool* right) {
  motion_.straight(cfg::kCellMm, cfg::kSearchSpeed, true);
  long sum_l = 0, sum_r = 0;
  int n = 0;
  while (motion_.busy()) {
    if (n < kSideSampleTicks && motion_.straightProgressMm() >= cfg::kCellMm - cfg::kSideLookAheadMm) {
      const WallReading w = io_.wallSensors();
      sum_l += w.l;
      sum_r += w.r;
      ++n;
    }
    io_.delayMs(1);
  }
  if (n == 0) return false;
  *left = sum_l / n > tuning_.thr_side;
  *right = sum_r / n > tuning_.thr_side;
  return true;
}

RunResult Runner::explore(maze::Explorer* ex) {
  bool have_side = false, side_l = false, side_r = false;
  while (true) {
    io_.delayMs(150);  // 歩行振動が収まりセンサ値が落ち着くまで待つ
    maze::WallObservation seen = senseWalls();
    if (have_side) {  // 前進の途中で読んだ横壁を使う
      seen.left = side_l;
      seen.right = side_r;
    }
    if (on_cell) on_cell(ex->position(), ex->heading(), seen, io_.wallSensors());
    const maze::Move mv = ex->step(seen);
    if (mv == maze::Move::kArrived) return RunResult::kOk;
    if (mv == maze::Move::kStuck) return RunResult::kStuck;
    if (seen.front && mv != maze::Move::kForward) {
      motion_.alignFront();
      motion_.wait();
    }
    doTurn(mv);
    ex->applyTurn(mv);
    have_side = forwardOneCell(&side_l, &side_r);
    ex->applyForward();
    if (io_.batteryVolts() < cfg::kBatteryCutoffV) return RunResult::kLowBattery;
  }
}

RunResult Runner::search(void (*on_goal)()) {
  maze_.reset();
  maze::Explorer ex(&maze_, kGoals, 4);
  RunResult r = explore(&ex);
  if (r != RunResult::kOk) return r;
  if (on_goal) on_goal();
  ex.setTargets(kStart, 1);
  r = explore(&ex);
  if (r != RunResult::kOk) return r;
  // スタート区画では北向きに戻しておく（最短走行の初期姿勢）
  const int rel = (static_cast<int>(maze::kNorth) - static_cast<int>(ex.heading()) + 4) & 3;
  if (rel == 1) doTurn(maze::Move::kTurnRight);
  if (rel == 2) doTurn(maze::Move::kTurnBack);
  if (rel == 3) doTurn(maze::Move::kTurnLeft);
  return RunResult::kOk;
}

RunResult Runner::fastRun() {
  maze::Step steps[128];
  const int n = maze::buildFastPath(maze_, kStart[0], maze::kNorth, kGoals, 4, steps, 128);
  if (n < 0) return RunResult::kNoPath;  // 未探索、または経路なし
  for (int i = 0; i < n; ++i) {
    // 旋回の前に前壁があれば位置と向きを補正する（探索と同じ。誤差の蓄積を防ぐ）
    if (steps[i].action != maze::Action::kStraight && senseWalls().front) {
      motion_.alignFront();
      motion_.wait();
    }
    switch (steps[i].action) {
      case maze::Action::kStraight:
        motion_.straight(cfg::kCellMm * steps[i].cells, cfg::kFastSpeed, true);
        motion_.wait();
        break;
      case maze::Action::kTurnLeft: doTurn(maze::Move::kTurnLeft); break;
      case maze::Action::kTurnRight: doTurn(maze::Move::kTurnRight); break;
      case maze::Action::kTurnBack: doTurn(maze::Move::kTurnBack); break;
    }
  }
  return RunResult::kOk;
}

float Runner::walkCells(int n) {
  const float start = motion_.distanceMm();
  motion_.straight(cfg::kCellMm * n, cfg::kSearchSpeed, false);
  motion_.wait();
  return motion_.distanceMm() - start;
}

}  // namespace mouse
