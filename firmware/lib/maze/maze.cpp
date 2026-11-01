#include "maze.h"

namespace maze {

void Maze::reset() {
  for (int x = 0; x < kSize; ++x)
    for (int y = 0; y < kSize; ++y) cells_[x][y] = 0;
  for (int i = 0; i < kSize; ++i) {
    setWall(Pos{static_cast<int8_t>(i), 0}, kSouth, true);
    setWall(Pos{static_cast<int8_t>(i), kSize - 1}, kNorth, true);
    setWall(Pos{0, static_cast<int8_t>(i)}, kWest, true);
    setWall(Pos{kSize - 1, static_cast<int8_t>(i)}, kEast, true);
  }
  // クラシックマウスのスタート区画は東側が壁、北にのみ開いている。
  setWall(Pos{0, 0}, kEast, true);
}

void Maze::setWall(Pos p, Dir d, bool exists) {
  if (!p.inside()) return;
  const uint8_t wall_bit = 1u << d;
  const uint8_t known_bit = 1u << (d + 4);
  cells_[p.x][p.y] = (cells_[p.x][p.y] & ~wall_bit) | (exists ? wall_bit : 0) | known_bit;

  const Pos n = p.neighbor(d);
  if (!n.inside()) return;
  const Dir od = opposite(d);
  const uint8_t n_wall = 1u << od;
  const uint8_t n_known = 1u << (od + 4);
  cells_[n.x][n.y] = (cells_[n.x][n.y] & ~n_wall) | (exists ? n_wall : 0) | n_known;
}

bool Planner::passable(const Maze& m, Pos p, Dir d, FloodMode mode) {
  if (!p.neighbor(d).inside()) return false;
  if (m.hasWall(p, d)) return false;
  if (mode == FloodMode::kKnownOnly && !m.isKnown(p, d)) return false;
  return true;
}

void Planner::flood(const Maze& m, const Pos* goals, int n_goals, FloodMode mode) {
  for (int x = 0; x < kSize; ++x)
    for (int y = 0; y < kSize; ++y) dist_[x][y] = kInf;

  // BFS（キューは固定長配列。各区画は高々1回だけ積まれる）
  Pos queue[kSize * kSize];
  int head = 0, tail = 0;
  for (int i = 0; i < n_goals; ++i) {
    const Pos g = goals[i];
    if (!g.inside() || dist_[g.x][g.y] == 0) continue;
    dist_[g.x][g.y] = 0;
    queue[tail++] = g;
  }
  while (head < tail) {
    const Pos p = queue[head++];
    const uint16_t nd = dist_[p.x][p.y] + 1;
    for (int k = 0; k < 4; ++k) {
      const Dir d = static_cast<Dir>(k);
      if (!passable(m, p, d, mode)) continue;
      const Pos n = p.neighbor(d);
      if (dist_[n.x][n.y] <= nd) continue;
      dist_[n.x][n.y] = nd;
      queue[tail++] = n;
    }
  }
}

bool Planner::nextDir(const Maze& m, Pos p, Dir heading, FloodMode mode, Dir* out) const {
  // 優先順: 直進, 右, 左, 後退
  static const int kOrder[4] = {0, 1, 3, 2};
  uint16_t best = dist_[p.x][p.y];
  bool found = false;
  for (int i = 0; i < 4; ++i) {
    const Dir d = rotate(heading, kOrder[i]);
    if (!passable(m, p, d, mode)) continue;
    const Pos n = p.neighbor(d);
    if (dist_[n.x][n.y] < best) {
      best = dist_[n.x][n.y];
      *out = d;
      found = true;
    }
  }
  return found;
}

static bool isGoal(Pos p, const Pos* goals, int n_goals) {
  for (int i = 0; i < n_goals; ++i)
    if (goals[i] == p) return true;
  return false;
}

bool shortestPathDetermined(const Maze& m, Pos start, const Pos* goals, int n_goals) {
  Planner optimistic, known;
  optimistic.flood(m, goals, n_goals, FloodMode::kSearch);
  known.flood(m, goals, n_goals, FloodMode::kKnownOnly);
  return known.distance(start) != kInf && known.distance(start) == optimistic.distance(start);
}

int buildFastPath(const Maze& m, Pos start, Dir heading, const Pos* goals, int n_goals,
                  Step* out, int max_steps) {
  Planner planner;
  planner.flood(m, goals, n_goals, FloodMode::kKnownOnly);
  if (planner.distance(start) == kInf) return -1;

  int n = 0;
  Pos p = start;
  Dir h = heading;
  auto push = [&](Action a, uint8_t cells) -> bool {
    if (a == Action::kStraight && n > 0 && out[n - 1].action == Action::kStraight) {
      ++out[n - 1].cells;
      return true;
    }
    if (n >= max_steps) return false;
    out[n++] = Step{a, cells};
    return true;
  };

  while (!isGoal(p, goals, n_goals)) {
    Dir d;
    if (!planner.nextDir(m, p, h, FloodMode::kKnownOnly, &d)) return -1;
    const int rel = (static_cast<int>(d) - static_cast<int>(h) + 4) & 3;
    if (rel == 1 && !push(Action::kTurnRight, 0)) return -1;
    if (rel == 2 && !push(Action::kTurnBack, 0)) return -1;
    if (rel == 3 && !push(Action::kTurnLeft, 0)) return -1;
    if (!push(Action::kStraight, 1)) return -1;
    h = d;
    p = p.neighbor(d);
  }
  return n;
}

}  // namespace maze
