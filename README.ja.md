# NextFFT Lab

**v0.1.0 Research Preview 候補** · [English](README.md)

2026年11月24日のプレプリント「The logarithmic exponent of finite Fourier transforms」を対象とする独立研究です。今回のサイクルでは、数学的構成の部分再現、固定サイズの Walsh–Hadamard テンプレートの測定、小規模回路の探索を行いました。[固定版プレプリント](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/paper.pdf)

## 研究成果

- **固定テンプレートの正当性。** 有限体 F₉₉₈₂₄₄₃₅₃ 上で行列ペンシル、小規模な Hermite 修復、共有ルーティングを検証しました。例外がゼロの固定テンプレートは、256要素の独立した512入力すべてで古典 Walsh–Hadamard と完全一致しました。例外を含む修復は、小規模な窓で別途検証しました。
- **性能測定。** 疎ルーティングとペンシルの短縮により、同じバッチで固定テンプレートは7.718秒から0.679秒になりました。同条件の古典 Walsh は0.0772秒でした。最適化後も8軸に対し1行あたり24回の軸変換が必要で、再帰の条件には達していません。
- **回路探索。** 探索範囲内の最良値は、H8で19二入力線形ゲート・共通スケール付き20算術演算、H16で共通スケール付き56算術演算でした。いずれも公開済みの比較基準と同じ値です。回路は有理数と有限体の両方で全基底を検証し、スケール復元は別に数えました。
- **未達事項。** 呼び出し数を削減する再帰テンプレート、一般長への再現、上流の Lean 形式証明のローカル検証は未完了です。

既知の結果の再現、NextFFTlab 独自の実装・測定、探索の否定的結果は[最終研究報告](docs/FINAL_REPORT.md)にまとめています。

## テストの実行

Python 3.10以上が必要です。リポジトリのルートに作成した仮想環境で実行します。

```sh
python -m pip install -e '.[dev,research]'
python -m pytest -q
python -m nextfft_lab.bench --max-power 7 --repeats 2
```

`research` は `z3-solver==4.15.4.0` を追加します。`.[dev]` のみで Z3 を入れていない場合、Z3回帰テスト1件がスキップされます。研究用CIの `research-z3` は Z3 を導入し、そのテストの実行と合格を確認します。

## 再現手順と資料

- [依存関係・実行コマンド・生データの索引](docs/REPRODUCIBILITY.md)
- [開発ロードマップと論文の対応箇所](docs/ROADMAP.md)
- [最適化の測定](docs/OPTIMIZATION.md)と[公開済み回路に対する探索](docs/RECORD_SEARCH.md)

古典的な巡回DFT・NTTと、二進テンソル上の Walsh–Hadamard は別の変換です。NumPy/SciPy の複素数ベンチマークも別の算術領域で測定しています。

## ライセンス

NextFFTlab 独自のコードと文書は [MIT](LICENSE) です。Jacob Sussman の H8 回路に由来するデータ2件には [第三者著作物の表示](results/record-circuits/NOTICE.md)と [Apache-2.0](results/record-circuits/LICENSE-APACHE-2.0.txt) が適用されます。

## 次期研究：一般長NTT・FFTと応用

[一般長研究計画・検証記録](docs/GENERAL_LENGTH_RESEARCH.md)では、原論文後半の補題の実行可能な検証と応用を扱います。有限体で全補助レジスタを復元するNewton変換、幾何格子の古典法との比較、小規模なパッキングとGood因子分解を検証しました。複素数版の数値誤差も測定しました。節約型再帰と論文全体の再現は未達です。[自律開発プロトコル](docs/AGENT_RESEARCH_PROTOCOL.md)
