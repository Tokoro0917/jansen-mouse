// 迷路データと足立法（歩数マップ）による経路計画。ハードウェア非依存。
#pragma once

#include <stdint.h>

namespace maze {

constexpr int kSize = 16;  // クラシック: 16x16 区画
constexpr uint16_t kInf = 0xFFFF;

enum Dir : uint8_t { kNorth = 0, kEast = 1, kSouth = 2, kWest = 3 };

inline Dir rotate(Dir d, int quarter_turns_cw) {
  return static_cast<Dir>((static_cast<int>(d) + quarter_turns_cw + 4) & 3);
}
inline Dir opposite(Dir d) { return rotate(d, 2); }
constexpr int8_t kDx[4] = {0, 1, 0, -1};
constexpr int8_t kDy[4] = {1, 0, -1, 0};

struct Pos {
  int8_t x;
  int8_t y;
  Pos neighbor(Dir d) const {
    return Pos{static_cast<int8_t>(x + kDx[d]), static_cast<int8_t>(y + kDy[d])};
  }
  bool inside() const { return x >= 0 && x < kSize && y >= 0 && y < kSize; }
  bool operator==(const Pos& o) const { return x == o.x && y == o.y; }
};

class Maze {
 public:
  Maze() { reset(); }

  // 外周壁とスタート区画（東壁）のみ既知の状態に戻す。
  void reset();

  // 壁の有無を確定させる（隣の区画の対応する壁も同時に更新）。
  void setWall(Pos p, Dir d, bool exists);

  bool hasWall(Pos p, Dir d) const { return (cell(p) >> d) & 1; }
  bool isKnown(Pos p, Dir d) const { return (cell(p) >> (d + 4)) & 1; }

  // 4方向すべての壁が確定している区画か。
  bool fullyKnown(Pos p) const { return (cell(p) & 0xF0) == 0xF0; }

  uint8_t raw(Pos p) const { return cell(p); }

 private:
  uint8_t cell(Pos p) const { return cells_[p.x][p.y]; }
  // bit0-3: 壁あり (N,E,S,W)  bit4-7: 確定済み (N,E,S,W)
  uint8_t cells_[kSize][kSize];
};

// 歩数マップの作り方
enum class FloodMode : uint8_t {
  kSearch,     // 未確定の壁は「無い」とみなす（探索走行）
  kKnownOnly,  // 未確定の壁は「有る」とみなす（最短走行）
};

class Planner {
 public:
  // goals から歩数マップを作る。
  void flood(const Maze& m, const Pos* goals, int n_goals, FloodMode mode);

  uint16_t distance(Pos p) const { return dist_[p.x][p.y]; }

  // 現在地・向きから次に進むべき方角を返す。到達不能なら false。
  // 歩数が同じなら 直進 > 左右 > 後退 を優先する（脚機構は旋回が遅いため）。
  bool nextDir(const Maze& m, Pos p, Dir heading, FloodMode mode, Dir* out) const;

 private:
  static bool passable(const Maze& m, Pos p, Dir d, FloodMode mode);
  uint16_t dist_[kSize][kSize];
};

// 最短走行用の動作列
enum class Action : uint8_t { kStraight, kTurnLeft, kTurnRight, kTurnBack };

struct Step {
  Action action;
  uint8_t cells;  // kStraight のときの区画数
};

// 既知の壁だけを使って start -> goals の動作列を作る。
// 返り値: 書き込んだ Step 数（到達不能なら -1）
int buildFastPath(const Maze& m, Pos start, Dir heading, const Pos* goals, int n_goals,
                  Step* out, int max_steps);

}  // namespace maze
