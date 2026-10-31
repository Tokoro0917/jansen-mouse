// 探索走行の意思決定。センサ値やモータは扱わず、
// 「区画中心で見えた壁」を受け取り「次の動作」を返すだけにしてホストで試験できるようにする。
#pragma once

#include "maze.h"

namespace maze {

struct WallObservation {
  bool left;
  bool front;
  bool right;
};

enum class Move : uint8_t { kForward, kTurnLeft, kTurnRight, kTurnBack, kArrived, kStuck };

class Explorer {
 public:
  Explorer(Maze* maze, const Pos* goals, int n_goals);

  // 探索の目的地を切り替える（ゴール探索 → スタートへ帰還 など）。
  void setTargets(const Pos* targets, int n_targets);

  // 区画中心での壁情報を反映し、次の動作を決める。
  // kForward 以外の旋回を返した場合、旋回後に kForward が必要（旋回と前進は呼び出し側で連続実行）。
  Move step(const WallObservation& seen);

  // 呼び出し側が実際に動いた後に自己位置を更新する。
  void applyTurn(Move turn);
  void applyForward();

  Pos position() const { return pos_; }
  Dir heading() const { return heading_; }

 private:
  bool atTarget() const;

  Maze* maze_;
  Planner planner_;
  Pos targets_[8];
  int n_targets_ = 0;
  Pos pos_{0, 0};
  Dir heading_ = kNorth;
};

}  // namespace maze
