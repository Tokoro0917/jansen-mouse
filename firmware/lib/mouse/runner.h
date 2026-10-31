// 探索走行・最短走行の手順。実機とシミュレーションで同じコードを使う。
#pragma once

#include "explorer.h"
#include "maze.h"
#include "motion.h"
#include "mouse_io.h"
#include "tuning.h"

namespace mouse {

enum class RunResult : uint8_t { kOk, kStuck, kLowBattery, kNoPath };

class Runner {
 public:
  Runner(MouseIO& io, Motion& motion, const WallTuning& tuning)
      : io_(io), motion_(motion), tuning_(tuning) {}

  // スタート → ゴール → スタート。on_goal はゴール到達時に呼ばれる（ブザー等）。
  RunResult search(void (*on_goal)() = nullptr);
  // 探索済みの既知壁だけで最短経路を走る
  RunResult fastRun();
  // n 区画直進し、オドメトリ上の走行距離 [mm] を返す（前進量の較正用）
  float walkCells(int n);

  maze::WallObservation senseWalls() const;
  const maze::Maze& maze() const { return maze_; }

  // 区画中心で壁を見るたびに呼ばれる（走行ログ用。実機ではシリアル出力に使える）
  void (*on_cell)(maze::Pos pos, maze::Dir heading, const maze::WallObservation& seen,
                  const WallReading& raw) = nullptr;

  static constexpr maze::Pos kGoals[4] = {{7, 7}, {7, 8}, {8, 7}, {8, 8}};
  static constexpr maze::Pos kStart[1] = {{0, 0}};

 private:
  // stop_when_determined: 最短経路が確定したら、その区画中心で探索をやめる（帰り道用）
  RunResult explore(maze::Explorer* ex, bool stop_when_determined = false);
  // 既知の壁だけで targets へ向かう（直線をまとめ、旋回前に前壁補正）。到着時の向きを返す。
  RunResult followKnownPath(maze::Pos from, maze::Dir heading, const maze::Pos* targets, int n,
                            float speed, maze::Dir* final_heading);
  void doTurn(maze::Move mv);
  void faceNorth(maze::Dir heading);

  MouseIO& io_;
  Motion& motion_;
  const WallTuning& tuning_;
  maze::Maze maze_;
};

}  // namespace mouse
