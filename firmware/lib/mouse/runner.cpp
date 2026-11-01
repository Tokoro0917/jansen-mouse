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

namespace {
// 次の区画の中心のこの距離手前で、その区画の壁を先読みする。
// 直進を続けるなら、ここで延長する。探索速度 90 mm/s の減速距離（90^2 / (2 x 150) = 27 mm）より短いので、
// 延長する時点で 77 mm/s 程度まで減速しかけているが、Trapezoid::extend はそこから再び加速する。
// 前壁はこの位置で見る。横壁はもっと手前で読んでおいたものを使う（下の kSideLookAheadMm）。
constexpr float kLookaheadMm = 20.0f;
constexpr int kSettleMs = 150;  // 停止後、歩行振動が収まりセンサ値が落ち着くまでの待ち
// 横壁は、左右センサの光が次の区画の横壁の真ん中に当たる瞬間（機体中心が次の区画中心の kSideLookAheadMm 手前）に読む。
// 光は機体中心より前の壁に当たるので、区画中心や先読み位置で読むと、前後に行き過ぎたときに
// その次の区画の壁を見てしまう。通過時に読めば、前後の誤差に ±78 mm まで耐える。
constexpr int kSideSampleTicks = 10;  // この tick 数の平均をとる（約 1 mm の区間）
}  // namespace

// 探索: 直進が続くあいだは止まらずに次の区画の壁を先読みし、旋回するときだけ区画中心で止まる。
RunResult Runner::explore(maze::Explorer* ex, bool stop_when_determined) {
  bool moving = false;   // 区画中心で止まらずに直進中か
  float planned = 0.0f;  // 今の直進の目標距離
  io_.delayMs(kSettleMs);
  maze::WallObservation seen = senseWalls();
  while (true) {
    if (on_cell) on_cell(ex->position(), ex->heading(), seen, io_.wallSensors());
    const maze::Move mv = ex->step(seen);
    if (stop_when_determined && mv != maze::Move::kArrived &&
        maze::shortestPathDetermined(maze_, kStart[0], kGoals, 4)) {
      motion_.wait();  // 今の区画の中心で止まる
      return RunResult::kOk;
    }
    if (moving) {
      if (mv == maze::Move::kForward) {
        motion_.extendStraight(cfg::kCellMm);  // 減速せずに次の区画へ
        planned += cfg::kCellMm;
      } else {
        motion_.wait();  // 区画中心で止まる
        moving = false;
      }
    }
    if (mv == maze::Move::kArrived) return RunResult::kOk;
    if (mv == maze::Move::kStuck) return RunResult::kStuck;
    if (!moving) {
      if (seen.front && mv != maze::Move::kForward) {
        motion_.alignFront();
        motion_.wait();
      }
      doTurn(mv);
      ex->applyTurn(mv);
      motion_.straight(cfg::kCellMm, cfg::kSearchSpeed, true);
      planned = cfg::kCellMm;
      moving = true;
    }
    // 次の区画の中心の手前まで進む。途中、光が次の区画の横壁の真ん中に当たる所で横壁を読む
    long sum_l = 0, sum_r = 0;
    int n = 0;
    while (motion_.busy() && motion_.straightProgressMm() < planned - kLookaheadMm) {
      if (n < kSideSampleTicks && motion_.straightProgressMm() >= planned - cfg::kSideLookAheadMm) {
        const WallReading w = io_.wallSensors();
        sum_l += w.l;
        sum_r += w.r;
        ++n;
      }
      io_.delayMs(1);
    }
    ex->applyForward();
    if (!motion_.busy()) {  // 先読み位置より前で止まった（前壁で停止した等）
      moving = false;
      io_.delayMs(kSettleMs);
    }
    seen = senseWalls();
    if (n > 0) {  // 前進の途中で読んだ横壁を使う
      seen.left = sum_l / n > tuning_.thr_side;
      seen.right = sum_r / n > tuning_.thr_side;
    }
    if (io_.batteryVolts() < cfg::kBatteryCutoffV) {
      motion_.stop();
      return RunResult::kLowBattery;
    }
  }
}

void Runner::faceNorth(maze::Dir heading) {
  const int rel = (static_cast<int>(maze::kNorth) - static_cast<int>(heading) + 4) & 3;
  if (rel == 1) doTurn(maze::Move::kTurnRight);
  if (rel == 2) doTurn(maze::Move::kTurnBack);
  if (rel == 3) doTurn(maze::Move::kTurnLeft);
}

RunResult Runner::search(void (*on_goal)()) {
  maze_.reset();
  maze::Explorer ex(&maze_, kGoals, 4);
  RunResult r = explore(&ex);
  if (r != RunResult::kOk) return r;
  if (on_goal) on_goal();
  // 帰り道も足立法で未知の区画を探索するが、最短経路が確定した時点でやめて既知の道で戻る
  ex.setTargets(kStart, 1);
  r = explore(&ex, true);
  if (r != RunResult::kOk) return r;
  maze::Dir heading = ex.heading();
  if (!(ex.position() == kStart[0])) {
    r = followKnownPath(ex.position(), heading, kStart, 1, cfg::kSearchSpeed, &heading);
    if (r != RunResult::kOk) return r;
  }
  faceNorth(heading);  // スタート区画では北向きに戻しておく（最短走行の初期姿勢）
  return RunResult::kOk;
}

RunResult Runner::followKnownPath(maze::Pos from, maze::Dir heading, const maze::Pos* targets,
                                  int n_targets, float speed, maze::Dir* final_heading) {
  // 最悪の場合（全区画を通り、毎区画で旋回）でも収まる大きさ
  static constexpr int kMaxSteps = 2 * maze::kSize * maze::kSize;
  maze::Step steps[kMaxSteps];
  const int n = maze::buildFastPath(maze_, from, heading, targets, n_targets, steps, kMaxSteps);
  if (n < 0) return RunResult::kNoPath;  // 未探索、または経路なし
  maze::Dir h = heading;
  for (int i = 0; i < n; ++i) {
    // 旋回の前に前壁があれば位置と向きを補正する（誤差の蓄積を防ぐ）
    if (steps[i].action != maze::Action::kStraight && senseWalls().front) {
      motion_.alignFront();
      motion_.wait();
    }
    switch (steps[i].action) {
      case maze::Action::kStraight:
        motion_.straight(cfg::kCellMm * steps[i].cells, speed, true);
        motion_.wait();
        break;
      case maze::Action::kTurnLeft: doTurn(maze::Move::kTurnLeft); h = maze::rotate(h, -1); break;
      case maze::Action::kTurnRight: doTurn(maze::Move::kTurnRight); h = maze::rotate(h, 1); break;
      case maze::Action::kTurnBack: doTurn(maze::Move::kTurnBack); h = maze::rotate(h, 2); break;
    }
  }
  if (final_heading) *final_heading = h;
  return RunResult::kOk;
}

RunResult Runner::fastRun() {
  return followKnownPath(kStart[0], maze::kNorth, kGoals, 4, cfg::kFastSpeed, nullptr);
}

float Runner::walkCells(int n) {
  const float start = motion_.distanceMm();
  motion_.straight(cfg::kCellMm * n, cfg::kSearchSpeed, false);
  motion_.wait();
  return motion_.distanceMm() - start;
}

}  // namespace mouse
