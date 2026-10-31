// このファイルは mechanism/ の `python -m jansen.cli header` で自動生成される。手で編集しないこと。
#pragma once

namespace mech {
constexpr float kLinkScaleMmPerUnit = 0.4500f;
constexpr int kCrankThrowsPerSide = 2;
constexpr float kStrideMmPerRev = 23.8782f;     // クランク1回転あたりの前進量
constexpr float kCrankHeightMm = 41.3252f;   // クランク中心の対地高さ
constexpr float kStepHeightMm = 10.1056f;
constexpr float kBodyLengthMm = 103.4f;
constexpr float kBodyWidthMm = 102.4f;
constexpr float kLegGroupPitchMm = 64.2f;  // 左右脚群の中心間距離
}  // namespace mech
