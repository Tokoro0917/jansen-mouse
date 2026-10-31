# Jansen Mouse — テオヤンセン機構で歩くクラシックマウス

タイヤの代わりに **テオヤンセン機構（Strandbeest の脚）** で歩く、マイクロマウス・クラシック競技（16×16 区画、1 区画 180 mm）用ロボットのプロジェクトです。

![leg](docs/images/leg.gif)

## 特徴

- **左右 2 モータ × 片側 4 脚（計 8 脚）**。片側 2 クランクスロー（180° 位相）× 前後鏡像ペア。
  常に片側 2 脚以上が接地する。
- 脚寸法は Theo Jansen の Holy Numbers を **0.45 mm/unit** に縮小。
  クランク 1 回転で **23.9 mm** 前進（1 区画 ≈ 7.5 回転）。
- 機体は **103 × 102 mm**、対角 146 mm。通路幅 168 mm の中で超信地旋回できることを、
  部品の積層・干渉を自動計算して確認している。
- 脚は滑るので、**向きはジャイロで常に閉ループ**、距離はクランク回転数 × ストライドで管理。
- 迷路アルゴリズム（足立法）と制御則はハードウェア非依存にし、**PC 上で単体試験**（ランダム迷路 30 面で探索 → 帰還 → 最短経路を検証）。
- 機構解析（Python）→ ファーム用定数ヘッダ / CAD 寸法・積層順・組立図 を**自動生成**し、寸法の二重管理をなくしている。

![組立図](docs/images/assembly.png)

## ディレクトリ構成

```
mechanism/   テオヤンセン機構の運動学シミュレーション (Python)
  jansen/      リンク計算・歩容解析・積層/干渉チェック・CLI
  tests/       pytest
firmware/    STM32F411 (Black Pill) 用ファームウェア (PlatformIO + Arduino)
  include/     config.h（ピン・調整値）, mechanism_params.h（自動生成）
  lib/maze/    迷路・歩数マップ・探索ロジック（ハード非依存）
  lib/control/ PID・台形速度プロファイル（ハード非依存）
  src/         ドライバ, 1kHz 走行制御, メイン
  test/        Unity による PC 上の単体試験
cad/         OpenSCAD のパラメトリック部品と組立図（*_generated.scad は自動生成）
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
python -m jansen.cli footprint              # 縮尺・スロー数ごとの機体外形
```

寸法を変えたら、ファームと CAD の定数も再生成します。

```bash
python -m jansen.cli header   -o ../firmware/include/mechanism_params.h
python -m jansen.cli scad     -o ../cad/links_generated.scad
python -m jansen.cli assembly -o ../cad/assembly_generated.scad
python -m jansen.cli report   -o ../docs/jansen_report.md
```

（縮尺・スロー数を変える場合は `--scale` / `--throws` を付けるか、`jansen/cli.py` の既定値を変更）

### CAD

```bash
cd cad
openscad -D 'PART="layout"' -o leg_parts.stl parts.scad   # 脚 1 本分の部品
openscad -o assembly.stl assembly_generated.scad          # 全体組立
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
- [x] パラメトリック CAD（積層順の自動決定・干渉チェック・組立図）
- [ ] 試作・実機でのパラメータ調整（センサ閾値、ストライド補正、PID ゲイン）
