// このファイルは mechanism/ の `python -m jansen.cli header` で自動生成される。手で編集しないこと。
#pragma once

namespace mech {
constexpr float kLinkScaleMmPerUnit = 0.4500f;
constexpr int kCrankThrowsPerSide = 2;
constexpr float kTravelMmPerRev = 56.9674f;  // クランク 1 回転あたりの胴体の前進量
constexpr float kStanceLengthMm = 23.8782f;   // 1 本の足の接地区間の長さ（参考値）
constexpr float kCrankHeightMm = 41.3252f;   // クランク中心の対地高さ
constexpr float kStepHeightMm = 10.1056f;
constexpr float kBodyLengthMm = 103.4f;
constexpr float kBodyWidthMm = 102.4f;
constexpr float kLegGroupPitchMm = 64.2f;  // 左右脚群の中心間距離

// 壁センサの位置（機体中心 = クランク軸の真下から。x 前, y 左）。脚の掃引域を避けた配置（jansen/body.py）
constexpr float kFrontSensorForwardMm = 50.0f;  // FL / FR: 中央の溝の中、真正面向き
constexpr float kFrontSensorLateralMm = 5.0f;
constexpr float kSideSensorForwardMm = 60.0f;   // L / R: 脚より前、真横向き
constexpr float kSideSensorLateralMm = 13.0f;

// 片側の胴体速度 / クランク角速度 [mm/rad] をクランク 1 回転で 64 等分した表
// （シミュレーション用。クランク角 0 は組立時の基準位相）
constexpr int kBodySpeedTableSize = 64;
constexpr float kBodySpeedTable[kBodySpeedTableSize] = {
    10.149f, 10.150f, 10.149f, 10.142f, 10.122f, 10.080f, 10.003f, 9.888f,
    9.712f, 9.482f, 9.164f, 8.777f, 8.274f, 7.686f, 6.949f, 6.031f,
    6.980f, 6.021f, 6.949f, 7.657f, 8.274f, 8.758f, 9.164f, 9.470f,
    9.712f, 9.882f, 10.003f, 10.077f, 10.122f, 10.142f, 10.149f, 10.150f,
    10.149f, 10.150f, 10.149f, 10.142f, 10.122f, 10.080f, 10.003f, 9.888f,
    9.712f, 9.482f, 9.164f, 8.777f, 8.274f, 7.686f, 6.949f, 6.031f,
    6.980f, 6.021f, 6.949f, 7.657f, 8.274f, 8.758f, 9.164f, 9.470f,
    9.712f, 9.882f, 10.003f, 10.077f, 10.122f, 10.142f, 10.149f, 10.150f,
};
}  // namespace mech
