# # 深度推定と前景分離を用いた360°3D映像のシームレス合成システム
(Seamless Synthesis for Simple 360° 3D Video Using Depth Estimation and Foreground Separation)

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C.svg?logo=pytorch&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8.svg?logo=opencv&logoColor=white)

## 概要
複数の安価な360度カメラを用いて、高品質な3Dパノラマ映像を生成するシステムを開発しました。  

従来の画素ベース合成では、境界での被写体の切断や映像の揺れが発生していましたが、  
本手法では **深度推定・動的前景分離・多段階フェード処理** を組み合わせることで、  
自然でシームレスな映像合成を実現しました。

---

## デモ (Demo)

### Before / After 比較
| 従来手法 (Before) | 提案手法 (After) |
|:---:|:---:|
| ![](docs/seamed_pic.png) | ![](docs/output_still_composite.png) |
| *物体の途中で不自然な切断が発生* | *物体の輪郭に沿った自然な合成* |



---

## 背景・課題
360°3D映像の制作には高価な専用機材（数百万円規模）が必要です。  
低コスト化のために複数カメラ合成が用いられますが、以下の課題がありました：

- 境界で人物が分断される
- フレームごとに境界が揺れる（VR酔いの原因）
- カメラの映り込みが発生

---

## 提案手法
以下の3つの技術により課題を解決しました。

### 1. 深度推定による前景分離
単眼深度推定モデル（Depth Anything V2）を用いて奥行きを推定し、  
物体単位での自然な合成を実現。

---

### 2. 動的閾値処理
深度分布の上位45%を閾値として採用し、環境に応じて前景を抽出。  
→ 屋内外でも安定した処理を実現。

---

### 3. 多段階フェード処理
- 部分フェード（50px）
- エッジフェード（100px）

を組み合わせることで、境界の不連続性を低減。

---

### 4. 幾何学的補正
- BF座標変換によるレンズ対応整理
- 天頂領域の誤検出を補正

---

## 担当・役割
本プロジェクトは卒業研究として**個人で開発**し、以下を担当しました：

- 撮影システム構築（THETA X ×3台、治具設計・3Dプリント）
- 深度推定モデル選定（ViTベース）
- 映像処理パイプラインの実装（Python）
- 主観評価実験および統計解析（ウィルコクソン検定）

---

## 結果
被験者10名による主観評価の結果：

- 境界の自然さ：大幅改善（p < 0.01）
- 映像の安定性：有意に向上（p < 0.05）
- 総合評価：提案手法が有意に高評価

---

## 🛠 技術スタック
- Python / PyTorch
- OpenCV / NumPy / MoviePy
- Depth Anything V2（ViTベース）
- CUDA（RTX 3060）

---

## 🚀 実行方法
```bash
git clone https://github.com/yoshiototora/360-video-synthesis-v1.git
cd 360-video-synthesis-v1
pip install -r requirements.txt
python main.py
