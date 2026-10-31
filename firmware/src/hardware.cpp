#include "hardware.h"

#include <SPI.h>

#include "config.h"

namespace hw {

// ---------------- モータ ----------------
static constexpr int kPwmResolution = 1000;

void motorsBegin() {
  pinMode(cfg::kPinMotorLDir, OUTPUT);
  pinMode(cfg::kPinMotorRDir, OUTPUT);
  analogWriteFrequency(20000);  // 可聴域外
  analogWriteResolution(10);
  motorsBrake();
}

static void driveOne(uint32_t pwm_pin, uint32_t dir_pin, float duty) {
  if (duty > 1.0f) duty = 1.0f;
  if (duty < -1.0f) duty = -1.0f;
  digitalWrite(dir_pin, duty < 0 ? HIGH : LOW);
  analogWrite(pwm_pin, static_cast<int>(fabsf(duty) * 1023.0f));
}

void motorsSet(float left, float right) {
  driveOne(cfg::kPinMotorLPwm, cfg::kPinMotorLDir, left * cfg::kMotorLSign);
  driveOne(cfg::kPinMotorRPwm, cfg::kPinMotorRDir, right * cfg::kMotorRSign);
}

void motorsBrake() {
  analogWrite(cfg::kPinMotorLPwm, 0);
  analogWrite(cfg::kPinMotorRPwm, 0);
}

// ---------------- エンコーダ ----------------
static volatile int32_t enc_l = 0;
static volatile int32_t enc_r = 0;

// 4 逓倍デコード表: index = (prev << 2) | curr
static const int8_t kQuad[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
static volatile uint8_t prev_l = 0, prev_r = 0;

static void isrLeft() {
  const uint8_t curr = (digitalRead(cfg::kPinEncLA) << 1) | digitalRead(cfg::kPinEncLB);
  enc_l += kQuad[(prev_l << 2) | curr] * cfg::kMotorLSign;
  prev_l = curr;
}

static void isrRight() {
  const uint8_t curr = (digitalRead(cfg::kPinEncRA) << 1) | digitalRead(cfg::kPinEncRB);
  enc_r += kQuad[(prev_r << 2) | curr] * cfg::kMotorRSign;
  prev_r = curr;
}

void encodersBegin() {
  const uint32_t pins[] = {cfg::kPinEncLA, cfg::kPinEncLB, cfg::kPinEncRA, cfg::kPinEncRB};
  for (uint32_t p : pins) pinMode(p, INPUT_PULLUP);
  prev_l = (digitalRead(cfg::kPinEncLA) << 1) | digitalRead(cfg::kPinEncLB);
  prev_r = (digitalRead(cfg::kPinEncRA) << 1) | digitalRead(cfg::kPinEncRB);
  attachInterrupt(digitalPinToInterrupt(cfg::kPinEncLA), isrLeft, CHANGE);
  attachInterrupt(digitalPinToInterrupt(cfg::kPinEncLB), isrLeft, CHANGE);
  attachInterrupt(digitalPinToInterrupt(cfg::kPinEncRA), isrRight, CHANGE);
  attachInterrupt(digitalPinToInterrupt(cfg::kPinEncRB), isrRight, CHANGE);
}

int32_t encoderLeft() { return enc_l; }
int32_t encoderRight() { return enc_r; }

// ---------------- 壁センサ ----------------
static volatile WallReading wall{0, 0, 0, 0};
static bool sample_front = true;

void wallSensorsBegin() {
  pinMode(cfg::kPinIrLedFront, OUTPUT);
  pinMode(cfg::kPinIrLedSide, OUTPUT);
  digitalWrite(cfg::kPinIrLedFront, LOW);
  digitalWrite(cfg::kPinIrLedSide, LOW);
  analogReadResolution(12);
}

void wallSensorsSample() {
  // 外乱光を打ち消すため、消灯時と点灯時の差分を取る
  const uint32_t led = sample_front ? cfg::kPinIrLedFront : cfg::kPinIrLedSide;
  const uint32_t a = sample_front ? cfg::kPinSensFL : cfg::kPinSensL;
  const uint32_t b = sample_front ? cfg::kPinSensFR : cfg::kPinSensR;
  const int off_a = analogRead(a);
  const int off_b = analogRead(b);
  digitalWrite(led, HIGH);
  delayMicroseconds(20);  // フォトトランジスタの立ち上がり待ち
  const int on_a = analogRead(a);
  const int on_b = analogRead(b);
  digitalWrite(led, LOW);
  if (sample_front) {
    wall.fl = on_a - off_a;
    wall.fr = on_b - off_b;
  } else {
    wall.l = on_a - off_a;
    wall.r = on_b - off_b;
  }
  sample_front = !sample_front;
}

WallReading wallSensors() {
  noInterrupts();
  WallReading r{wall.fl, wall.l, wall.r, wall.fr};
  interrupts();
  return r;
}

// ---------------- IMU ----------------
static constexpr uint8_t kRegUserCtrl = 0x6A;
static constexpr uint8_t kRegPwrMgmt1 = 0x6B;
static constexpr uint8_t kRegGyroConfig = 0x1B;
static constexpr uint8_t kRegGyroZH = 0x47;
static constexpr uint8_t kRegWhoAmI = 0x75;
static constexpr float kGyroLsbPerDps = 16.4f;  // ±2000 dps
static float gyro_bias = 0.0f;
static const SPISettings kImuSpi(1000000, MSBFIRST, SPI_MODE3);

static void imuWrite(uint8_t reg, uint8_t val) {
  SPI.beginTransaction(kImuSpi);
  digitalWrite(cfg::kPinImuCs, LOW);
  SPI.transfer(reg & 0x7F);
  SPI.transfer(val);
  digitalWrite(cfg::kPinImuCs, HIGH);
  SPI.endTransaction();
}

static uint8_t imuRead(uint8_t reg, uint8_t* buf = nullptr, int n = 1) {
  uint8_t first = 0;
  SPI.beginTransaction(kImuSpi);
  digitalWrite(cfg::kPinImuCs, LOW);
  SPI.transfer(reg | 0x80);
  for (int i = 0; i < n; ++i) {
    const uint8_t v = SPI.transfer(0);
    if (i == 0) first = v;
    if (buf) buf[i] = v;
  }
  digitalWrite(cfg::kPinImuCs, HIGH);
  SPI.endTransaction();
  return first;
}

bool imuBegin() {
  pinMode(cfg::kPinImuCs, OUTPUT);
  digitalWrite(cfg::kPinImuCs, HIGH);
  SPI.begin();
  imuWrite(kRegPwrMgmt1, 0x80);  // リセット
  delay(100);
  imuWrite(kRegPwrMgmt1, 0x01);  // PLL クロック
  imuWrite(kRegUserCtrl, 0x10);  // I2C 無効化 (SPI 専用)
  imuWrite(kRegGyroConfig, 0x18);
  delay(10);
  const uint8_t who = imuRead(kRegWhoAmI);
  return who == 0x12 /* ICM-20602 */ || who == 0x70 /* MPU-6500 */;
}

static float imuRawZ() {
  uint8_t b[2];
  imuRead(kRegGyroZH, b, 2);
  return static_cast<int16_t>((b[0] << 8) | b[1]) / kGyroLsbPerDps;
}

void imuCalibrate(int samples) {
  float sum = 0.0f;
  for (int i = 0; i < samples; ++i) {
    sum += imuRawZ();
    delay(1);
  }
  gyro_bias = sum / samples;
}

float imuYawRateDps() { return imuRawZ() - gyro_bias; }

// ---------------- UI ----------------
void uiBegin() {
  pinMode(cfg::kPinLed, OUTPUT);
  pinMode(cfg::kPinBuzzer, OUTPUT);
  pinMode(cfg::kPinBtnMode, INPUT_PULLUP);
  pinMode(cfg::kPinBtnStart, INPUT_PULLUP);
  led(false);
}

void beep(int freq_hz, int ms) { tone(cfg::kPinBuzzer, freq_hz, ms); }
void led(bool on) { digitalWrite(cfg::kPinLed, on ? LOW : HIGH); }
bool modeButton() { return digitalRead(cfg::kPinBtnMode) == LOW; }
bool startButton() { return digitalRead(cfg::kPinBtnStart) == LOW; }

float batteryVolts() { return analogRead(cfg::kPinBattery) * (3.3f / 4095.0f) * 3.0f; }

}  // namespace hw
