# Jansen Mouse — テオヤンセン機構で歩くクラシックマウス

タイヤの代わりに **テオヤンセン機構（Strandbeest の脚）** で歩く、マイクロマウス・クラシック競技（16×16 区画、1 区画 180 mm）用ロボットのプロジェクトです。

![leg](docs/images/leg.gif)

## 特徴

- **左右 2 モータ × 片側 6 脚（計 12 脚）**。片側 3 クランクスロー（120° 位相）× 前後鏡像ペア。
  常に片側 2 脚以上が接地し、胴体の上下動は計算上 0.04 mm。
- 脚寸法は Theo Jansen の Holy Numbers を **0.55 mm/unit** に縮小。
  クランク 1 回転で **29.2 mm** 前進（1 区画 ≈ 6.17 回転）。
- 脚は滑るので、**向きはジャイロで常に閉ループ**、距離はクランク回転数 × ストライドで管理。
- 迷路アルゴリズム（足立法）と制御則はハードウェア非依存にし、**PC 上で単体試験**（ランダム迷路 30 面で探索 → 帰還 → 最短経路を検証）。
- 機構解析（Python）→ ファーム用定数ヘッダ / CAD 寸法 を**自動生成**し、寸法の二重管理をなくしている。

## ディレクトリ構成

```
mechanism/   テオヤンセン機構の運動学シミュレーション (Python)
  jansen/      リンク計算・歩容解析・CLI
  tests/       pytest
firmware/    STM32F411 (Black Pill) 用ファームウェア (PlatformIO + Arduino)
  include/     config.h（ピン・調整値）, mechanism_params.h（自動生成）
  lib/maze/    迷路・歩数マップ・探索ロジック（ハード非依存）
  lib/control/ PID・台形速度プロファイル（ハード非依存）
  src/         ドライバ, 1kHz 走行制御, メイン
  test/        Unity による PC 上の単体試験
cad/         OpenSCAD のパラメトリック部品（links_generated.scad は自動生成）
docs/        設計資料・部品表・解析結果
```

## クイックスタート

### 機構シミュレーション

```bash
cd mechanism
pip install -r requirements.txt
python -m pytest -q
python -m jansen.cli report                 # 歩容指標とリンク長
python -m jansen.cli plot -o ../docs/images # 足先軌跡・接地数グラフ
```

寸法を変えたら、ファームと CAD の定数も再生成します。

```bash
python -m jansen.cli header --scale 0.55 -o ../firmware/include/mechanism_params.h
python -m jansen.cli scad   --scale 0.55 -o ../cad/links_generated.scad
python -m jansen.cli report --scale 0.55 -o ../docs/jansen_report.md
```

### ファームウェア

```bash
cd firmware
pio test -e native          # PC 上で迷路・制御ロジックの試験
pio run -e blackpill_f411ce # 実機向けビルド
pio run -e blackpill_f411ce -t upload   # ST-LINK で書き込み
```

操作: **MODE** ボタンでモード選択 → **START** で実行。

| モード | 内容 |
|---|---|
| 0 | センサ確認（USB シリアルへ壁センサ・ジャイロ・エンコーダ・電池電圧を出力） |
| 1 | 探索走行（スタート → ゴール → スタート） |
| 2 | 最短走行（探索済みの壁のみで経路を作り、直線をまとめて走る） |
| 3 | ストライド較正（5 区画直進し、実測との比を求める） |

## ドキュメント

- [設計資料](docs/design.md) — 機構寸法の決め方、レギュレーション適合、制御方針
- [ハードウェア](docs/hardware.md) — 部品表、ピン配置、組み立て・調整手順
- [機構解析レポート](docs/jansen_report.md) — 自動生成のリンク長表と歩容指標

## 開発状況

- [x] 機構の運動学シミュレーションと寸法決定
- [x] 迷路探索・最短経路アルゴリズム（PC 上で検証済み）
- [x] 実機ファームウェア（ビルド確認済み・実機未調整）
- [x] パラメトリック CAD
- [ ] 試作・実機でのパラメータ調整（センサ閾値、ストライド補正、PID ゲイン）
