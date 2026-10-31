#include <unity.h>

#include <stdint.h>

#include "explorer.h"
#include "maze.h"

using namespace maze;

static const Pos kGoals[4] = {{7, 7}, {7, 8}, {8, 7}, {8, 8}};
static const Pos kStart[1] = {{0, 0}};

// ---- 試験用の「真の迷路」生成（穴掘り法 + ループ追加） ----
static uint32_t rng_state;
static uint32_t rnd() {
  rng_state ^= rng_state << 13;
  rng_state ^= rng_state >> 17;
  rng_state ^= rng_state << 5;
  return rng_state;
}

static void makeTrueMaze(Maze* m, uint32_t seed, int extra_openings) {
  rng_state = seed;
  for (int x = 0; x < kSize; ++x)
    for (int y = 0; y < kSize; ++y)
      for (int d = 0; d < 4; ++d) m->setWall(Pos{(int8_t)x, (int8_t)y}, (Dir)d, true);

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
  for (int i = 0; i < extra_openings; ++i) {
    const Pos p{(int8_t)(1 + rnd() % (kSize - 2)), (int8_t)(1 + rnd() % (kSize - 2))};
    m->setWall(p, (Dir)(rnd() % 4), false);
  }
  // ゴール 2x2 の内部は壁なし、スタートは北のみ開放
  m->setWall(Pos{7, 7}, kNorth, false);
  m->setWall(Pos{7, 7}, kEast, false);
  m->setWall(Pos{8, 8}, kSouth, false);
  m->setWall(Pos{8, 8}, kWest, false);
  m->setWall(Pos{0, 0}, kEast, true);
  m->setWall(Pos{0, 0}, kNorth, false);
}

static WallObservation look(const Maze& truth, Pos p, Dir h) {
  return WallObservation{truth.hasWall(p, rotate(h, -1)), truth.hasWall(p, h),
                         truth.hasWall(p, rotate(h, 1))};
}

// 探索を実行し、到達できたら移動区画数を返す（失敗 -1）
static int runSearch(const Maze& truth, Explorer* ex) {
  for (int moves = 0; moves < 4000; ++moves) {
    const Move mv = ex->step(look(truth, ex->position(), ex->heading()));
    if (mv == Move::kArrived) return moves;
    if (mv == Move::kStuck) return -1;
    ex->applyTurn(mv);
    TEST_ASSERT_FALSE_MESSAGE(truth.hasWall(ex->position(), ex->heading()), "walked into wall");
    ex->applyForward();
  }
  return -1;
}

// ---- tests ----
void test_reset_has_boundary_and_start_walls() {
  Maze m;
  TEST_ASSERT_TRUE(m.hasWall(Pos{0, 0}, kWest));
  TEST_ASSERT_TRUE(m.hasWall(Pos{0, 0}, kSouth));
  TEST_ASSERT_TRUE(m.hasWall(Pos{0, 0}, kEast));
  TEST_ASSERT_TRUE(m.hasWall(Pos{1, 0}, kWest));  // 隣接区画にも反映
  TEST_ASSERT_TRUE(m.hasWall(Pos{15, 15}, kNorth));
  TEST_ASSERT_FALSE(m.isKnown(Pos{5, 5}, kNorth));
}

void test_set_wall_updates_neighbor() {
  Maze m;
  m.setWall(Pos{3, 3}, kNorth, true);
  TEST_ASSERT_TRUE(m.hasWall(Pos{3, 4}, kSouth));
  TEST_ASSERT_TRUE(m.isKnown(Pos{3, 4}, kSouth));
  m.setWall(Pos{3, 4}, kSouth, false);
  TEST_ASSERT_FALSE(m.hasWall(Pos{3, 3}, kNorth));
}

void test_flood_on_empty_maze_is_manhattan() {
  Maze m;
  Planner p;
  p.flood(m, kGoals, 4, FloodMode::kSearch);
  TEST_ASSERT_EQUAL_UINT16(0, p.distance(Pos{8, 8}));
  // (0,0) は東が壁なので北回り: 7 + 7 = 14
  TEST_ASSERT_EQUAL_UINT16(14, p.distance(Pos{0, 0}));
  // 既知のみモードでは未探索区画は通れない
  p.flood(m, kGoals, 4, FloodMode::kKnownOnly);
  TEST_ASSERT_EQUAL_UINT16(kInf, p.distance(Pos{0, 0}));
}

void test_search_reaches_goal_and_returns_on_random_mazes() {
  for (uint32_t seed = 1; seed <= 30; ++seed) {
    Maze truth;
    makeTrueMaze(&truth, seed * 2654435761u, 20);
    Maze known;
    Explorer ex(&known, kGoals, 4);
    TEST_ASSERT_TRUE(runSearch(truth, &ex) > 0);
    ex.setTargets(kStart, 1);
    TEST_ASSERT_TRUE(runSearch(truth, &ex) > 0);
    TEST_ASSERT_TRUE(ex.position() == (Pos{0, 0}));

    // 探索済みの壁だけで最短経路が引け、真の迷路上で壁にぶつからない
    Step steps[256];
    const int n = buildFastPath(known, Pos{0, 0}, ex.heading(), kGoals, 4, steps, 256);
    TEST_ASSERT_TRUE(n > 0);
    Pos p{0, 0};
    Dir h = ex.heading();
    for (int i = 0; i < n; ++i) {
      switch (steps[i].action) {
        case Action::kTurnLeft: h = rotate(h, -1); break;
        case Action::kTurnRight: h = rotate(h, 1); break;
        case Action::kTurnBack: h = rotate(h, 2); break;
        case Action::kStraight:
          for (int c = 0; c < steps[i].cells; ++c) {
            TEST_ASSERT_FALSE(truth.hasWall(p, h));
            p = p.neighbor(h);
          }
          break;
      }
    }
    bool at_goal = false;
    for (const Pos& g : kGoals) at_goal |= (g == p);
    TEST_ASSERT_TRUE(at_goal);
  }
}

void test_fast_path_merges_straights() {
  Maze m;
  // x=0 列をまっすぐ北へ、(0,7) から東へ 7 区画で (7,7)
  for (int y = 0; y < kSize; ++y)
    for (int x = 0; x < kSize; ++x)
      for (int d = 0; d < 4; ++d) m.setWall(Pos{(int8_t)x, (int8_t)y}, (Dir)d, true);
  for (int y = 0; y < 7; ++y) m.setWall(Pos{0, (int8_t)y}, kNorth, false);
  for (int x = 0; x < 7; ++x) m.setWall(Pos{(int8_t)x, 7}, kEast, false);
  Step steps[16];
  const int n = buildFastPath(m, Pos{0, 0}, kNorth, kGoals, 4, steps, 16);
  TEST_ASSERT_EQUAL_INT(3, n);
  TEST_ASSERT_EQUAL(Action::kStraight, steps[0].action);
  TEST_ASSERT_EQUAL_UINT8(7, steps[0].cells);
  TEST_ASSERT_EQUAL(Action::kTurnRight, steps[1].action);
  TEST_ASSERT_EQUAL_UINT8(7, steps[2].cells);
}

void setUp() {}
void tearDown() {}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_reset_has_boundary_and_start_walls);
  RUN_TEST(test_set_wall_updates_neighbor);
  RUN_TEST(test_flood_on_empty_maze_is_manhattan);
  RUN_TEST(test_search_reaches_goal_and_returns_on_random_mazes);
  RUN_TEST(test_fast_path_merges_straights);
  return UNITY_END();
}
