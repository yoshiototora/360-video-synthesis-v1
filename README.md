# 深度推定を用いた360°映像の高品質合成システム
(High-quality 360° Video Synthesis System using Depth Estimation)

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C.svg?logo=pytorch&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8.svg?logo=opencv&logoColor=white)

## 📝 概要
360°映像における不自然な合成境界を解消し、**物体単位で自然な映像合成を実現するシステム**を開発しました。

深度推定を用いた前景分離と動的閾値処理を組み合わせることで、従来手法では困難だった「物体の輪郭に沿った自然な境界生成」を可能にしています。

---

## 🎬 デモ (Demo)

### Before / After 比較
| 従来手法 (Before) | 提案手法 (After) |
|:---:|:---:|
| ![](docs/before.png) | ![](docs/after.png) |
| *物体の途中で不自然な切断が発生* | *物体の輪郭に沿った自然な合成* |

### 動画デモ
[▶️ デモ映像を再生する](https://github.com/user-attachments/assets/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)

---

## 👤 担当・役割
本プロジェクトは個人で研究・開発を行い、以下のプロセスをすべて担当しました。

- **アルゴリズム設計**: 深度推定（Depth Anything V2）をベースとした前景分離ロジックの構築
- **動的閾値ロジックの実装**: 環境変化に適応するための深度分布に基づいた自動閾値決定の実装
- **フェード処理の実装**: 境界の違和感を最小限に抑える多段階フェード処理の設計
- **動画処理パイプラインの構築**: OpenCVを用いた映像読み込みから合成、音声再結合までの自動化・最適化

---

## 🚨 背景・課題
360°映像（正距円筒図法）において、複数カメラの映像を合成する際に以下の問題が発生します。

- カメラ間の視差および露出差による不自然なつなぎ目
- 物体の途中での不自然な切断（ゴースト現象や消失）
- 直線的で目立つ合成境界

特に従来手法（固定領域による合成）では、物体の形を無視して機械的に切断されるため、視覚的な違和感が大きいという課題がありました。

## 💡 提案手法
以下の3つの技術を組み合わせることで、従来の課題を解決しました。

1. **深度推定による前景分離**
   単眼画像から深度を推定し、前景（近い物体）と背景を分離。画素単位ではなく「物体単位」での合成を実現。
2. **動的閾値の導入**
   シーンごとの深度分布に応じて合成の境界を動的に決定。屋内外や被写体の距離が変化する環境にも柔軟に適応。
3. **多段階フェード処理**
   分離した境界部分にフェードを適用し、不連続な色の変化を視覚的に緩和。

## 📈 評価
被験者による主観評価実験において、従来手法（固定境界法）と比較して**「境界の自然さ」「物体の切断の少なさ」**の項目で有意な改善を確認しました。

## 🛠 技術スタック
- **言語**: Python
- **ライブラリ**: PyTorch, OpenCV, Transformers
- **モデル**: Depth Anything V2 (Small)
- **ツール**: MoviePy (音声合成用)

## 🚀 実行方法
```bash
# リポジトリのクローン
git clone [https://github.com/yoshiototora/360-video-synthesis-v1.git](https://github.com/yoshiototora/360-video-synthesis-v1.git)
cd 360-video-synthesis-v1

# 依存ライブラリのインストール
pip install -r requirements.txt

# 実行
python main.py
