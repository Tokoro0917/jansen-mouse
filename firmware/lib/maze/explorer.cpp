#include "explorer.h"

namespace maze {

Explorer::Explorer(Maze* maze, const Pos* goals, int n_goals) : maze_(maze) {
  setTargets(goals, n_goals);
}

void Explorer::setTargets(const Pos* targets, int n_targets) {
  n_targets_ = n_targets > 8 ? 8 : n_targets;
  for (int i = 0; i < n_targets_; ++i) targets_[i] = targets[i];
}

bool Explorer::atTarget() const {
  for (int i = 0; i < n_targets_; ++i)
    if (targets_[i] == pos_) return true;
  return false;
}

Move Explorer::step(const WallObservation& seen) {
  maze_->setWall(pos_, rotate(heading_, -1), seen.left);
  maze_->setWall(pos_, heading_, seen.front);
  maze_->setWall(pos_, rotate(heading_, 1), seen.right);
  if (atTarget()) return Move::kArrived;

  planner_.flood(*maze_, targets_, n_targets_, FloodMode::kSearch);
  Dir d;
  if (!planner_.nextDir(*maze_, pos_, heading_, FloodMode::kSearch, &d)) return Move::kStuck;
  switch ((static_cast<int>(d) - static_cast<int>(heading_) + 4) & 3) {
    case 0: return Move::kForward;
    case 1: return Move::kTurnRight;
    case 2: return Move::kTurnBack;
    default: return Move::kTurnLeft;
  }
}

void Explorer::applyTurn(Move turn) {
  if (turn == Move::kTurnRight) heading_ = rotate(heading_, 1);
  if (turn == Move::kTurnLeft) heading_ = rotate(heading_, -1);
  if (turn == Move::kTurnBack) heading_ = rotate(heading_, 2);
}

void Explorer::applyForward() { pos_ = pos_.neighbor(heading_); }

}  // namespace maze
