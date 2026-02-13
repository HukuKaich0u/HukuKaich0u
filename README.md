# HukuKaich0u

![GitHub Metrics](./github-metrics.svg)

## Setup

1. GitHubでこのリポジトリの `Settings` -> `Secrets and variables` -> `Actions` を開く
2. `New repository secret` から `METRICS_TOKEN` を作成
3. トークンは classic PAT で `public_repo`（privateを含めるなら `repo`）を付与
4. `Actions` タブから `Metrics` ワークフローを `Run workflow` で手動実行

初回実行後、`github-metrics.svg` が更新されてREADMEに表示されます。
