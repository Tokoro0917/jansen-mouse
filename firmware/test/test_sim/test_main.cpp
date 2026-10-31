// 実機と同じ走行制御・探索コードを模擬ロボット上で動かす統合試験。
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <unity.h>

#include "motion.h"
#include "runner.h"
#include "sim_robot.h"

using namespace maze;
using sim::SimParams;
using sim::SimRobot;

// ---- 試験用の迷路 ----
static uint32_t rng_state;
static uint32_t rnd() {
  rng_state ^= rng_state << 13;
  rng_state ^= rng_state >> 17;
  rng_state ^= rng_state << 5;
  return rng_state;
}

static void closeAll(Maze* m) {
  for (int x = 0; x < kSize; ++x)
    for (int y = 0; y < kSize; ++y)
      for (int d = 0; d < 4; ++d) m->setWall(Pos{(int8_t)x, (int8_t)y}, (Dir)d, true);
}

static void openAll(Maze* m) {
  m->reset();
  for (int x = 0; x < kSize; ++x)
    for (int y = 0; y < kSize; ++y)
      for (int d = 0; d < 4; ++d) {
        const Pos p{(int8_t)x, (int8_t)y};
        if (p.neighbor((Dir)d).inside()) m->setWall(p, (Dir)d, false);
      }
}

static void makeRandomMaze(Maze* m, uint32_t seed) {
  rng_state = seed;
  closeAll(m);
  bool visited[kSize][kSize] = {};
  Pos stack[kSize * kSize];
  int sp = 0;
  stack[sp++] = Pos{0, 0};
  visited[0][0] = true;
  while (sp > 0) {
    const Pos p = stack[sp - 1];
    Dir cand[4];
    int nc = 0;
    for (int d = 0; d < 4; ++d) {
      const Pos n = p.neighbor((Dir)d);
      if (n.inside() && !visited[n.x][n.y]) cand[nc++] = (Dir)d;
    }
    if (nc == 0) {
      --sp;
      continue;
    }
    const Dir d = cand[rnd() % nc];
    m->setWall(p, d, false);
    const Pos n = p.neighbor(d);
    visited[n.x][n.y] = true;
    stack[sp++] = n;
  }
  for (int i = 0; i < 20; ++i) {
    const Pos p{(int8_t)(1 + rnd() % (kSize - 2)), (int8_t)(1 + rnd() % (kSize - 2))};
    m->setWall(p, (Dir)(rnd() % 4), false);
  }
  m->setWall(Pos{7, 7}, kNorth, false);
  m->setWall(Pos{7, 7}, kEast, false);
  m->setWall(Pos{8, 8}, kSouth, false);
  m->setWall(Pos{8, 8}, kWest, false);
  m->setWall(Pos{0, 0}, kEast, true);
  m->setWall(Pos{0, 0}, kNorth, false);
}

// 区画中央に置いて壁センサの基準値を測る（実機の調整手順と同じ）
static mouse::WallTuning calibrate() {
  Maze closed;
  closeAll(&closed);
  SimParams p;
  SimRobot robot(closed, p);
  robot.placeAtCell(5, 5, 90.0f);
  mouse::WallTuning t;
  mouse::Motion motion(robot, t);
  robot.attach(&motion);
  motion.begin();
  long sum_l = 0, sum_r = 0, sum_f = 0;
  const int n = 200;
  for (int i = 0; i < n; ++i) {
    robot.delayMs(1);
    const mouse::WallReading w = robot.wallSensors();
    sum_l += w.l;
    sum_r += w.r;
    sum_f += w.fl + w.fr;
  }
  t.side_ref_l = sum_l / n;
  t.side_ref_r = sum_r / n;
  t.front_ref_sum = sum_f / n;
  return t;
}

struct Rig {
  Rig(const Maze& truth, SimParams p, mouse::WallTuning t)
      : tuning(t), robot(truth, p), motion(robot, tuning), runner(robot, motion, tuning) {
    robot.attach(&motion);
    motion.begin();
  }
  mouse::WallTuning tuning;
  SimRobot robot;
  mouse::Motion motion;
  mouse::Runner runner;
};

static SimRobot* g_trace_robot = nullptr;
static const Maze* g_trace_truth = nullptr;
static bool g_trace = getenv("SIM_TRACE") != nullptr;  // 区画ごとの走行ログ（不一致・衝突のみ）
static void traceCell(Pos pos, Dir h, const WallObservation& seen, const mouse::WallReading& raw) {
  if (!g_trace) return;
  const bool tl = g_trace_truth->hasWall(pos, rotate(h, -1)), tf = g_trace_truth->hasWall(pos, h),
             tr = g_trace_truth->hasWall(pos, rotate(h, 1));
  static int last_coll = 0;
  const int coll = g_trace_robot->collisions() - last_coll;
  last_coll = g_trace_robot->collisions();
  if (getenv("TRACE_ALL") == nullptr && !coll && seen.left == tl && seen.front == tf && seen.right == tr) return;
  printf("  coll+%d (%d,%d) h%d pose(%.0f,%.0f,%.1f) cell(%d,%d) seen %d%d%d truth %d%d%d raw FL%d L%d R%d FR%d%s\n",
         coll, pos.x, pos.y, h, g_trace_robot->x(), g_trace_robot->y(), g_trace_robot->headingDeg(),
         g_trace_robot->cellX(), g_trace_robot->cellY(), seen.left, seen.front, seen.right, tl, tf, tr,
         raw.fl, raw.l, raw.r, raw.fr,
         (seen.left != tl || seen.front != tf || seen.right != tr) ? "  <-- MISMATCH" : "");
}

static float headingError(float actual_deg, float expected_deg) {
  float e = fmodf(actual_deg - expected_deg, 360.0f);
  if (e > 180) e -= 360;
  if (e < -180) e += 360;
  return fabsf(e);
}

// ---- tests ----
static mouse::WallTuning g_tuning;

void test_calibration_values_are_sane() {
  printf("calibrated: side L %d R %d, front sum %d\n", g_tuning.side_ref_l, g_tuning.side_ref_r,
         g_tuning.front_ref_sum);
  TEST_ASSERT_TRUE(g_tuning.side_ref_l > g_tuning.thr_side * 2);
  TEST_ASSERT_TRUE(g_tuning.front_ref_sum / 2 > g_tuning.thr_front * 4);
}

void test_straight_five_cells_in_corridor() {
  Maze corridor;
  closeAll(&corridor);
  for (int y = 0; y < 7; ++y) corridor.setWall(Pos{0, (int8_t)y}, kNorth, false);
  Rig rig(corridor, SimParams{}, g_tuning);
  rig.motion.straight(5 * cfg::kCellMm, cfg::kSearchSpeed, true);
  rig.motion.wait();
  printf("straight: cell (%d,%d) offset %.1f mm heading %.1f deg t=%.1fs\n", rig.robot.cellX(),
         rig.robot.cellY(), rig.robot.offsetFromCellCenter(), rig.robot.headingDeg(), rig.robot.timeS());
  TEST_ASSERT_EQUAL_INT(0, rig.robot.collisions());
  TEST_ASSERT_EQUAL_INT(5, rig.robot.cellY());
  TEST_ASSERT_TRUE(rig.robot.offsetFromCellCenter() < 15.0f);
  TEST_ASSERT_TRUE(headingError(rig.robot.headingDeg(), 90.0f) < 3.0f);
}

void test_spin_turns_return_to_heading() {
  Maze open;
  openAll(&open);
  Rig rig(open, SimParams{}, g_tuning);
  rig.robot.placeAtCell(5, 5, 90.0f);
  const float turns[] = {90, 90, -90, 180, -90, -180};
  float expected = 90.0f;
  for (float t : turns) {
    rig.motion.turn(t);
    rig.motion.wait();
    expected += t;
    printf("  turn %+.0f: true %.2f est %.2f expected %.0f t=%.2fs\n", t, rig.robot.headingDeg(),
           rig.motion.yawDeg() + 90.0f, expected, rig.robot.timeS());
  }
  printf("turns: heading %.1f (expected %.1f) offset %.1f mm\n", rig.robot.headingDeg(), expected,
         rig.robot.offsetFromCellCenter());
  TEST_ASSERT_EQUAL_INT(0, rig.robot.collisions());
  TEST_ASSERT_TRUE(headingError(rig.robot.headingDeg(), expected) < 3.0f);
  TEST_ASSERT_TRUE(rig.robot.offsetFromCellCenter() < 10.0f);
}

static void runFullMission(uint32_t seed, float travel_scale) {
  Maze truth;
  makeRandomMaze(&truth, seed);
  SimParams p;
  p.travel_scale = travel_scale;
  p.seed = seed;
  Rig rig(truth, p, g_tuning);
  g_trace_robot = &rig.robot;
  g_trace_truth = &truth;
  rig.runner.on_cell = traceCell;

  const mouse::RunResult r = rig.runner.search();
  // 探索で記録した壁が真の迷路と食い違っていないか
  int wrong = 0, known = 0;
  for (int x = 0; x < kSize; ++x)
    for (int y = 0; y < kSize; ++y)
      for (int d = 0; d < 4; ++d) {
        const Pos q{(int8_t)x, (int8_t)y};
        if (!rig.runner.maze().isKnown(q, (Dir)d)) continue;
        ++known;
        if (rig.runner.maze().hasWall(q, (Dir)d) != truth.hasWall(q, (Dir)d)) ++wrong;
      }
  printf("seed %u scale %.2f: search %d, t=%.0fs, back at (%d,%d) offset %.1f mm, collisions %d, "
         "wrong walls %d/%d\n",
         (unsigned)seed, travel_scale, (int)r, rig.robot.timeS(), rig.robot.cellX(), rig.robot.cellY(),
         rig.robot.offsetFromCellCenter(), rig.robot.collisions(), wrong, known);
  TEST_ASSERT_EQUAL_INT((int)mouse::RunResult::kOk, (int)r);
  TEST_ASSERT_EQUAL_INT(0, wrong);
  TEST_ASSERT_EQUAL_INT(0, rig.robot.collisions());
  TEST_ASSERT_EQUAL_INT(0, rig.robot.cellX());
  TEST_ASSERT_EQUAL_INT(0, rig.robot.cellY());

  // 探索をやめた時点でも、既知の壁だけの最短経路が真の最短経路と同じ長さであること
  Planner known_planner, truth_planner;
  known_planner.flood(rig.runner.maze(), mouse::Runner::kGoals, 4, FloodMode::kKnownOnly);
  truth_planner.flood(truth, mouse::Runner::kGoals, 4, FloodMode::kKnownOnly);
  printf("  shortest path: known %d / true %d cells\n", (int)known_planner.distance(Pos{0, 0}),
         (int)truth_planner.distance(Pos{0, 0}));
  TEST_ASSERT_EQUAL_UINT16(truth_planner.distance(Pos{0, 0}), known_planner.distance(Pos{0, 0}));

  const float t0 = rig.robot.timeS();
  const mouse::RunResult f = rig.runner.fastRun();
  printf("  fast run %d, t=%.0fs, at (%d,%d), collisions %d\n", (int)f, rig.robot.timeS() - t0,
         rig.robot.cellX(), rig.robot.cellY(), rig.robot.collisions());
  TEST_ASSERT_EQUAL_INT((int)mouse::RunResult::kOk, (int)f);
  TEST_ASSERT_EQUAL_INT(0, rig.robot.collisions());
  TEST_ASSERT_TRUE(rig.robot.cellX() >= 7 && rig.robot.cellX() <= 8);
  TEST_ASSERT_TRUE(rig.robot.cellY() >= 7 && rig.robot.cellY() <= 8);
}

void test_full_mission_nominal() {
  runFullMission(1, 1.00f);
  runFullMission(2, 1.00f);
}

void test_full_mission_with_travel_error() {
  // 較正しきれずに前進量が 3 % 短い / 長い場合
  runFullMission(3, 0.97f);
  runFullMission(4, 1.03f);
}

// 多数の迷路で回す（時間がかかるので SIM_EXTENDED=1 のときだけ）
void test_full_mission_extended() {
  if (getenv("SIM_EXTENDED") == nullptr) {
    TEST_IGNORE_MESSAGE("SIM_EXTENDED=1 で実行");
  }
  const float scales[] = {0.97f, 1.00f, 1.03f};
  for (uint32_t seed = 10; seed < 22; ++seed) runFullMission(seed, scales[seed % 3]);
}

void setUp() {}
void tearDown() {}

int main() {
  g_tuning = calibrate();
  UNITY_BEGIN();
  RUN_TEST(test_calibration_values_are_sane);
  RUN_TEST(test_straight_five_cells_in_corridor);
  RUN_TEST(test_spin_turns_return_to_heading);
  RUN_TEST(test_full_mission_nominal);
  RUN_TEST(test_full_mission_with_travel_error);
  RUN_TEST(test_full_mission_extended);
  return UNITY_END();
}
