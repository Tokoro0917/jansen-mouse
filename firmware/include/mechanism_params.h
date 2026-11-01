// このファイルは mechanism/ の `python -m jansen.cli header` で自動生成される。手で編集しないこと。
#pragma once

namespace mech {
constexpr float kLinkScaleMmPerUnit = 0.4000f;
constexpr int kCrankThrowsPerSide = 3;
constexpr float kTravelMmPerRev = 54.4353f;  // クランク 1 回転あたりの胴体の前進量
constexpr float kStanceLengthMm = 21.2250f;   // 1 本の足の接地区間の長さ（参考値）
constexpr float kCrankHeightMm = 36.7336f;   // クランク中心の対地高さ
constexpr float kStepHeightMm = 8.9828f;
constexpr float kBodyLengthMm = 92.7f;
constexpr float kBodyWidthMm = 113.6f;
constexpr float kLegGroupPitchMm = 69.8f;  // 左右脚群の中心間距離

// 壁センサの位置（機体中心 = クランク軸の真下から。x 前, y 左）。脚の掃引域を避けた配置（jansen/body.py）
// 4 本とも基板の前端より内側の裏に下げる（前に突き出さない）
constexpr float kFrontSensorForwardMm = 34.0f;  // FL / FR: 中央の溝の端、真正面向き
constexpr float kFrontSensorLateralMm = 9.0f;
constexpr float kSideSensorForwardMm = 37.0f;   // L / R: 内側から斜め前向き
constexpr float kSideSensorLateralMm = 5.0f;
constexpr float kSideSensorAngleDeg = 75.0f;  // 前 = 0, 真横 = 90
constexpr float kSideSensorSin = 0.9659f;
// 区画中央にいるとき、左右センサの光が横の壁に当たる点の前方距離と、そこまでの光の長さ
constexpr float kSideLookAheadMm = 58.2f;
constexpr float kSideBeamToWallMm = 81.8f;

// 片側の胴体速度 / クランク角速度 [mm/rad] をクランク 1 回転で 64 等分した表
// （シミュレーション用。クランク角 0 は組立時の基準位相）
constexpr int kBodySpeedTableSize = 64;
constexpr float kBodySpeedTable[kBodySpeedTableSize] = {
    8.287f, 8.270f, 9.516f, 9.639f, 9.724f, 9.761f, 9.754f, 9.703f,
    9.604f, 8.223f, 8.281f, 8.282f, 8.227f, 8.123f, 8.078f, 8.107f,
    8.117f, 8.108f, 8.078f, 8.117f, 8.227f, 8.280f, 8.281f, 8.227f,
    9.604f, 9.699f, 9.754f, 9.761f, 9.724f, 9.644f, 9.516f, 8.268f,
    8.287f, 8.252f, 8.161f, 8.063f, 8.100f, 8.116f, 8.113f, 8.091f,
    8.072f, 8.194f, 8.269f, 8.288f, 8.250f, 9.560f, 9.674f, 9.740f,
    9.764f, 9.742f, 9.674f, 9.565f, 8.250f, 8.287f, 8.269f, 8.199f,
    8.072f, 8.089f, 8.113f, 8.116f, 8.100f, 8.065f, 8.161f, 8.249f,
};
}  // namespace mech
