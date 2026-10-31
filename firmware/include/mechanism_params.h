// このファイルは mechanism/ の `python -m jansen.cli header` で自動生成される。手で編集しないこと。
#pragma once

namespace mech {
constexpr float kLinkScaleMmPerUnit = 0.5500f;
constexpr int kCrankThrowsPerSide = 3;
constexpr float kStrideMmPerRev = 29.1844f;     // クランク1回転あたりの前進量
constexpr float kCrankHeightMm = 50.5086f;   // クランク中心の対地高さ
constexpr float kStepHeightMm = 12.3513f;
}  // namespace mech
