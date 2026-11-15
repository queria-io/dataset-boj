# dataset-boj

Queria のデータセット `boj`（日本銀行 時系列統計）のリポジトリです。データセットの説明は [docs/index.md](docs/index.md) にあります。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # fdl checkout → python main.py → fdl commit
```

毎回全系列を取り直します。API に負荷をかけないよう、リクエストの間を 1 秒以上空けています。
