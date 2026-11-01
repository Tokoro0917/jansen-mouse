#include <unity.h>

#include "pid.h"
#include "trapezoid.h"

using control::Pid;
using control::Trapezoid;

void test_trapezoid_reaches_target_without_overshoot() {
  Trapezoid t;
  t.start(180.0f, 200.0f, 400.0f);
  float max_v = 0;
  int ticks = 0;
  while (!t.done() && ticks < 100000) {
    const float v = t.update(0.001f);
    if (v > max_v) max_v = v;
    ++ticks;
  }
  TEST_ASSERT_TRUE(t.done());
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 180.0f, t.position());
  TEST_ASSERT_TRUE(max_v <= 200.0f + 1e-3f);
  // 理論時間 = 180/200 + 200/400 = 1.4 s 程度
  TEST_ASSERT_INT_WITHIN(60, 1400, ticks);
}

void test_trapezoid_negative_distance() {
  Trapezoid t;
  t.start(-90.0f, 360.0f, 720.0f);
  while (!t.done()) TEST_ASSERT_TRUE(t.update(0.001f) <= 0.0f);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, -90.0f, t.position());
}

void test_trapezoid_extend_keeps_speed() {
  Trapezoid t;
  t.start(180.0f, 60.0f, 150.0f);
  while (t.position() < 160.0f) t.update(0.001f);  // 減速が始まる前（残り 20 mm）
  const float v_before = t.update(0.001f);
  t.extend(180.0f);
  float v_min = v_before;
  while (t.position() < 300.0f) {
    const float v = t.update(0.001f);
    if (v < v_min) v_min = v;
  }
  TEST_ASSERT_FLOAT_WITHIN(0.5f, v_before, v_min);  // 延長しても減速しない
  while (!t.done()) t.update(0.001f);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 360.0f, t.position());
}

void test_pid_output_is_limited_and_integral_does_not_wind_up() {
  Pid pid(1.0f, 10.0f, 0.0f, 1.0f);
  for (int i = 0; i < 10000; ++i) TEST_ASSERT_TRUE(pid.update(100.0f, 0.001f) <= 1.0f);
  // 誤差が反転したら直ちに出力も反転方向へ動く（積分が溜まりすぎていない）
  const float out = pid.update(-2.0f, 0.001f);
  TEST_ASSERT_TRUE(out < 0.0f);
}

void setUp() {}
void tearDown() {}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_trapezoid_reaches_target_without_overshoot);
  RUN_TEST(test_trapezoid_negative_distance);
  RUN_TEST(test_trapezoid_extend_keeps_speed);
  RUN_TEST(test_pid_output_is_limited_and_integral_does_not_wind_up);
  return UNITY_END();
}
