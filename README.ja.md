# NextFFT Lab（日本語）

2026年11月24日のOpenAIの有限フーリエ変換に関するプレプリントを対象とする独立した検証プロジェクトです。現段階では古典的アルゴリズムの比較基盤のみを実装しています。新手法の実装・高速化・数学的証明の独立検証は未完了です。

## 実行方法

Python 3.10以上で、`python -m pip install -e '.[dev]'` を実行後、`python -m pytest -q` でテスト、`python -m nextfft_lab.bench --max-power 12 --repeats 5` でベンチマークを実行できます。

有限体上の直接DFTを正解参照とし、古典的radix-2 NTTおよびBluestein変換を比較します。複素浮動小数点のNumPy/SciPyは別の測定系列です。異なる算術領域の時間を直接比較して高速化を主張しません。

研究計画・参考文献・未検証事項は [docs/research.md](docs/research.md) を参照してください。実用化の第一候補は厳密な多項式乗算です。
