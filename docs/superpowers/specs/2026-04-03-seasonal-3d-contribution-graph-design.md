# Seasonal 3D Contribution Graph Design

## Goal

既存の GitHub profile README 構成を維持したまま、`3D Contribution Graph` の見た目を季節ごとの配色に変更し、表示サイズも少し大きくする。

今回の変更対象は次の 2 点に限定する。

- 3D graph 内の各日セルを、属する季節ごとの色で表現する
- 3D graph の表示スケールを上げて主役感を強める

他の metrics セクションや README レイアウトは変更しない。

## Seasonal Rules

季節区切りは固定で扱う。

- 春: 3月, 4月, 5月
- 夏: 6月, 7月, 8月
- 秋: 9月, 10月, 11月
- 冬: 12月, 1月, 2月

`現在日付` に応じてテーマ全体を切り替えるのではなく、`1年分の graph の中で日付ごとに季節色を割り当てる`。

## Chosen Approach

既存の `lowlighter/metrics` による `github-metrics.svg` 生成を維持し、その直後に既存の post-processor を拡張して季節別配色とスケール変更を適用する。

理由:

- README の構成を変えなくてよい
- 毎日の自動更新フローを維持できる
- 既存の 3D graph を活かしたまま、見た目だけを大きく変えられる

## Architecture

フローは以下の通り。

1. GitHub Actions が `lowlighter/metrics` を使って `github-metrics.svg` を生成する
2. post-processor が 3D contribution graph セクションを検出する
3. 各キューブが表す日付をグラフ上の位置から復元する
4. 月から季節を判定する
5. 季節 × contribution level に応じた配色を適用する
6. graph の表示スケールを拡大する

## Visual Design

### Seasonal Palette Direction

各季節は contribution level ごとの段階色を持つ。

#### Spring

- pastel pink を基調とする
- 低活動日はごく薄い桜色
- 高活動日は少し深い rose pink

#### Summer

- pastel yellow を基調とする
- 低活動日はクリーム色
- 高活動日は黄緑寄りになりすぎない柔らかい yellow

#### Autumn

- red / orange / maple 系を基調とする
- 低活動日は薄い peach
- 高活動日は紅葉っぽい濃い red-orange

#### Winter

- pale blue / white を基調とする
- 低活動日は白に近い blue-gray
- 高活動日は冷たい水色

### Depth Direction

既存の top / left / right face の分離は維持する。
各季節色に対して面ごとの明暗差を付け、季節色を保ったまま立体感を出す。

### Size Direction

現在の graph root の `scale(4)` を少し拡大し、graph の見た目を今より大きくする。

変更は最小限に留める。

- 右側の commit streaks セクションを潰さない
- SVG 全体レイアウトは崩さない
- graph だけが少し大きく見える状態にする

## Date Mapping Strategy

3D contribution graph の各セルは、週単位の列と曜日単位の行に対応している。
post-processor は isometric cube 群の並び順を使って、各セルに対応する日付を復元する。

前提:

- graph は 1 年分の contribution calendar である
- 左から右へ週が進む
- 各列の中で曜日順にセルが並ぶ

この並び順から day index を求め、対象 year の calendar へ対応付ける。

## Component Design

### 1. Post-Processor Extension

既存の [postprocess_3d_contribution_graph.py](../../../scripts/postprocess_3d_contribution_graph.py) を拡張する。

責務:

- graph 内セルの順序解析
- month から season の判定
- season × level の top face color 決定
- side face color の導出
- graph root transform のスケール拡大

### 2. Tests

追加または更新するテスト内容:

- month → season 判定
- season × level の色選択
- 実 SVG に対して四季の色が混在すること
- 再実行しても崩れないこと

## Error Handling

以下の場合は workflow を失敗扱いにする。

- graph セクションが見つからない
- キューブ順序から日付復元ができない
- 季節別色置換の対象件数が異常に少ない
- スケール変更対象の root transform が見つからない

## Testing Plan

ローカル確認では次を行う。

- unit test で季節判定を確認
- `github-metrics.svg` に後処理を適用して四季の色が現れることを確認
- graph の scale が変わることを確認
- 再適用しても差分が増えないことを確認

## Non-Goals

今回やらないこと:

- README レイアウト変更
- 3D graph を別画像へ差し替えること
- レーダーチャートやドーナツの追加
- contribution データの生成元変更

## Open Risk

現在の SVG 構造だけでは、セル位置から日付復元を 100% 安定して行うための追加調整が必要になる可能性がある。

このリスクに対しては、検出条件とテストを強めて、期待した順序解析ができない場合は fail-fast する。
