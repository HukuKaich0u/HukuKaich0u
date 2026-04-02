# 3D Contribution Graph Visual Refresh Design

## Goal

GitHub profile README 内の `3D Contribution Graph` だけを、参照先プロフィールに近い印象へ寄せる。

今回の変更対象は次の 2 点に限定する。

- グリーン基調の配色を、淡いカラフルな配色へ変更する
- 立体ブロックの凹凸感を今より強くする

他の metrics セクション、README 構成、画像参照方法は変更しない。

## Current State

現在の生成フローは GitHub Actions の [`.github/workflows/metrics.yml`](../../../.github/workflows/metrics.yml) が `lowlighter/metrics` を実行し、`github-metrics.svg` を再生成する形になっている。

そのため `github-metrics.svg` を直接編集しても、次回の workflow 実行時に再生成されて上書きされる。

## Chosen Approach

`lowlighter/metrics` による SVG 生成はそのまま維持し、生成直後に `3D Contribution Graph` 部分だけを後処理する。

この後処理は workflow の新規ステップで実行し、`github-metrics.svg` のうち isometric contribution calendar に該当する SVG ノードだけを対象にする。

この方式を選ぶ理由:

- 自動更新後も見た目が維持される
- README の構成を変えずに済む
- `lowlighter/metrics` だけでは出しにくい配色と陰影の調整を行える
- 変更対象を 3D graph に限定できる

## Architecture

フローは以下の通り。

1. GitHub Actions が `lowlighter/metrics` を使って `github-metrics.svg` を生成する
2. 後処理スクリプトが `github-metrics.svg` を読み込む
3. `3D Contribution Graph` に対応する SVG 要素だけを検出する
4. contribution level ごとの色と陰影表現を置き換える
5. 更新済みの `github-metrics.svg` をそのまま README から参照する

## Component Design

### 1. Workflow Update

`metrics.yml` に `github-metrics.svg` 生成後の新規ステップを追加する。

役割:

- SVG 後処理スクリプトを実行する
- 対象セクションが見つからない場合は job を失敗させる

### 2. SVG Post-Processor

小さい専用スクリプトを追加する。責務は `3D Contribution Graph` の見た目補正のみとする。

想定責務:

- isometric calendar セクションの検出
- contribution intensity ごとの色マッピング
- 明部・暗部のフィルタまたは面ごとの色差強化
- 必要なら高さ表現の増幅

スクリプトは SVG 全体を書き換えるのではなく、対象ノードに限定して変換する。

## Visual Design

### Color Direction

現在の緑単色ベースをやめ、淡いカラフルな配色にする。

方向性:

- 低い contribution は淡いグレーまたはごく薄い色で残す
- 中間レベルは pastel blue, mint, peach, lavender などを使う
- 高い contribution は彩度を少しだけ上げるが、ネオン調にはしない
- 全体は柔らかいトーンに保つ

配色は contribution level ごとに固定マップを持たせる。

### Depth Direction

凹凸感を強くするため、上面・左面・右面の明暗差を今より広げる。

方向性:

- 上面は最も明るくする
- 左右の側面は上面より暗くする
- 面ごとの差を現状より大きくする
- contribution level が高いブロックほど高さ差が視覚的に分かるようにする

実装上は、既存の `brightness1` / `brightness2` に相当する見た目をより強くするか、面ごとの色差を直接置換する。

## Detection Strategy

後処理対象の誤検知を避けるため、以下の複数条件で isometric calendar 部分を特定する。

- `Contributions calendar` セクション配下であること
- isometric cube を構成する `<g transform=...>` 群を含むこと
- 既存の contribution color 群が使われていること

曖昧な全置換は行わない。

## Error Handling

以下の場合は workflow を失敗扱いにする。

- 対象セクションが見つからない
- 想定した SVG 構造が崩れている
- 色置換や陰影変換の対象件数が異常に少ない

これにより、`lowlighter/metrics` 側の出力構造が変わったときに静かに壊れるのを防ぐ。

## Testing Plan

ローカル確認では次を行う。

- 既存の `github-metrics.svg` に後処理を適用する
- 対象セクションの見た目だけが変わることを diff で確認する
- README に変更が入らないことを確認する
- 置換対象数が想定範囲に収まることを確認する

workflow 上では、後処理後に差分が発生した `github-metrics.svg` を通常通りコミット対象に含める。

## Non-Goals

今回やらないこと:

- README レイアウト変更
- 他の metrics セクションの配色変更
- 3D graph を別画像へ差し替えること
- contribution データ自体の生成ロジック変更

## Open Risk

`lowlighter/metrics@latest` は将来的に SVG 構造が変わる可能性がある。その場合、後処理スクリプトの検出条件が合わなくなる恐れがある。

このリスクに対しては、対象未検出時に workflow を失敗させることで早期に気づけるようにする。
