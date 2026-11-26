# NextFFT Lab 最終研究報告

**v0.1.0 Research Preview 候補 · 2026-11-27**

## 要約

有限体上の固定サイズの Walsh–Hadamard テンプレートを実装し、512本の独立した256点入力が古典実装と完全に一致することを確認した。疎ルーティングとペンシルの縮小により、同じ入力に対する試作の実行時間を7.718秒から0.679秒に短縮した。この測定での古典実装は0.0772秒だった。H8とH16の回路探索では公開済みの比較値を更新できなかった。今回の探索と最適化は終了し、コード、測定値、検証範囲を再現できる形で保全する。

**English summary.** The preview verifies one fixed-size Walsh–Hadamard template over a finite field. Sparse routing and a smaller pencil accelerated the prototype, while the classical implementation remained faster on the measured workload. Bounded searches retained published H8 and H16 circuit counts. Recursion, general-length transforms and an independent proof verification remain open. [Optimization evidence](OPTIMIZATION.md) · [Circuit search evidence](RECORD_SEARCH.md)

## 1. 研究目的

OpenAIのプレプリントが与える有限フーリエ変換の上界について、構成要素をコードと対応付け、限定した条件での正当性と実行コストを確かめる。実測では演算領域、入力、出力をそろえ、線形ゲート数、スカラー演算数、軸変換呼び出し相当数、実行時間、メモリを区別した。小規模回路については、公開済みの比較対象を再現し、既知回路の近傍に改善があるかを調べた。NextFFT Labは独立した研究プロジェクトである。

## 2. 原論文の概要

2026年11月24日付の *The logarithmic exponent of finite Fourier transforms* は、同じ位数 N の J 個の有限アーベル群のフーリエ変換を対象とする。係数体では N が可逆で、各群の指数に対応する原始根が存在すると仮定する。任意の定数 a, b による au+bv を1ゲートとするモデルで、ゲート数の下界は Ω(JN√log N)、任意の ε > 0 に対する上界は Oε(JN(1+log N)^(1/2+ε)) である。上界の構成には予測、スペクトル修復、共有ルーティングと再帰が含まれる。漸近的なゲート数評価から有限サイズでの実行時間やメモリ使用量は決まらない。 [固定版の原論文](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/paper.pdf)

本研究は主に F₉₉₈₂₄₄₃₅₃ 上の素数テンソル変換の二進の場合、すなわち (ℤ/2ℤ)ᵏ の Walsh–Hadamard 変換を扱った。比較用の巡回DFT、radix-2 NTT、Bluesteinと畳み込みは別系列であり、複素浮動小数点のNumPy/SciPy測定も区別した。 [論文の補題・Lean定理との対応](ROADMAP.md)

## 3. 実装した構成と正当性

| 構成 | 実装・検証範囲 |
|---|---|
| クエリ冪による予測 | 整数カウントの参照式と、指示多項式から得た打ち切り級数評価を比較した。3ビットの窓では全64組のクエリ・シフトを照合した。 |
| 行列ペンシル | アフィン線形因子から疎な巡回シフトと位相を構成した。b=2,4,8 の小規模ケースで全基底列と格子外の体の値について Lᵇ=pI を確認した。 |
| Hermite修復 | 既知の例外位置に対するVandermonde検査と持ち上げを実装した。非ゼロの例外がある3ビットの小規模例では独立した座標置換と全512基底で一致した。周波数ごとに変わる例外集合や例外なしのケースも検証した。 |
| 二進の共有ルーティング | 可換クエリの積を位相補正と軸交換で Walsh 行列に戻し、長さ64の式を全基底列で照合した。重み付き矩形のラベル転送と自由矩形の組合せも小規模に検証した。 |
| 固定テンプレート | m=3、L=q=2、D=2、A=8、f=1 で、行列ペンシル、共有ルーティング、前後の変換を接続した。256点の全512入力行で独立した反復型 Walsh と完全に一致し、4ラベルの逆変換・正規化は別の基底テストで確認した。この構成の予測窓 [−4,7] は例外を生じない。 |

予測、ペンシル、修復、ルーティングは原論文に由来する構成の実装である。固定テンプレートの一致と非ゼロ例外の修復は、別々の実験で確認した。 [ソースと検証の対応](ROADMAP.md) · [予測データ](../results/gate1-components.json) · [ペンシル・修復データ](../results/gate2-pencil.json) · [固定テンプレートデータ](../results/gate3-kernel.json)

## 4. 最適化による性能改善

512本の独立した256点入力について、Windows 11 x86-64、Ryzen 7 5800X、CPython 3.13.3、単一アルゴリズムスレッドで各実装を3回測定した。表の時間は同一条件での適用時間の中央値である。行間MACは行の混合に使った積和のみを示す。

| 実装 | ペンシル段数 | 軸変換呼び出し相当数 | 行間MAC | 実行時間 | ピークワーキングセット |
|---|---:|---:|---:|---:|---:|
| 最適化前の固定テンプレート | 16 | 163,840 | 3,276,800 | 7.718秒 | 49.9 MiB |
| 疎ルーティングのみ | 16 | 12,288 | 3,276,800 | 0.829秒 | 44.2 MiB |
| 疎ルーティングと縮小ペンシル | 4 | 12,288 | 1,703,936 | 0.679秒 | 48.8 MiB |
| 古典 Walsh | — | 4,096 | — | 0.0772秒 | 39.6 MiB |

試作内の改善は約11.4倍である。疎ルーティングが軸変換を減らし、ペンシルの縮小が行の混合を減らした。最適化版は同条件の古典 Walsh の約8.8倍の時間を要した。別の m=15 の単一シフト実験では、4,096レーンの暗黙ペンシル評価が遷移を明示的に展開した版の213.77 msから46.36 msになった。この測定は単一のスカラーフィールド評価を対象とする。 [測定方法とアブレーション](OPTIMIZATION.md) · [基準](../results/optimization-baseline.json) · [疎ルーティング](../results/optimization-routing-only.json) · [縮小ペンシル](../results/optimization-compact.json) · [古典 Walsh](../results/optimization-classical.json)

## 5. 構造的ボトルネック

- **再帰に必要な節約**。40件のスケジュール見積もりのうち、入力だけの1 GiB条件に収まる見積もりは11件だった。調べたスケジュールに σ/W < A^(3/4) を満たすものはなく、最適化した固定テンプレートも1行当たり24回の軸変換相当を要した。A=8 の古典的な軸ごとの変換は8回である。
- **シフト数と独立入力**。m=15 の最狭対称窓 [1,14] では例外が全シフトのうち周波数ごとに2個になる。この端点例外の構造を利用し、ビットごとの補数で結ばれる各ペアから高々1シフトを選ぶと、指定の最悪例外率の上限を守りながら32,768シフトを6,750まで減らせる。最小性はこの端点予測器、独立行の割当て、全クエリ組と指定の例外率に限る。全32,768周波数を検査した。1シフト当たり4,096レーンの見積もりでは、ラベル当たり27,648,000行を要する。
- **明示的なアドレス配置**。採用した配置で m=15 なら A≥30 で、f=1 でも32ビットで詰めた入力1行だけで最低4 GiBとなる。係数体の拡大、全シフトの同時保持、修復とルーティングに要する領域は別に考慮する。これらは検証した構成と配置のコストである。 [窓・バッチ・メモリの導出](OPTIMIZATION.md) · [一般化の適用範囲](CIRCUIT_RESEARCH.md)

## 6. 線形回路探索と先行研究

最初の探索では、ランク1分解に基づく限定文法の範囲でH4の7ゲート、H8の22ゲートを得た。これらは既知の比較値である。Sussmanの19ゲートH8を512点に展開し、全512基底で検証した。二入力ゲートは4,608から3,648、加減算と定数乗算の合計は4,608から4,352へ減った。Pythonでの中央値は公開回路を用いた展開が741 µs、古典反復型が344 µsだった。 [回路合成と計数](CIRCUIT_RESEARCH.md) · [回路・実測データ](../results/circuit-search.json)

先行研究との比較では、Alman–Raoの算術演算数とSussmanの二入力ゲート数を区別した。固定版のSussman系列では、H16の3/4系列は52ゲートでスケール付き60算術演算、5/6系列のH16はスケール付き56算術演算だった。最良のH8は19ゲート、共通スケール付きでは20算術演算だった。スケール復元の乗算は本体の演算数と分けて記録した。公開記録近傍の探索で残った回路は有理数と F₉₉₈₂₄₄₃₅₃ のどちらでも全基底で照合した。 [Alman–Rao](https://arxiv.org/abs/2211.06459) · [Sussmanの固定版](https://github.com/jacobalansussman/wht-fewer-operations/tree/bbb7f830d8c5612465a9922ace566750ce6d09d2) · [算術・ゲート・復元の対照表](RECORD_SEARCH.md)

## 7. 否定的結果と研究上の限界

- 局所置換と再結合、共通部分式除去、制限付きビーム探索で16,293候補を評価した。H8の射影閉包では、一補助線削除11件と二削除・一置換25,080件を、採用した方向集合について全件検査した。H16の53算術演算以下、H8の18ゲート以下、H8のスケール付き19算術演算以下を満たす回路は、この探索では得られなかった。
- 固定DAGのスケール指数を [−2,2] に制約したSMT検査では、H16の52ゲートDAGを53算術演算に収める解は **UNSAT** だった。同じDAGについて59算術演算以下を問う検査はタイムアウトで **UNKNOWN** だった。これらは当該DAGと指数範囲の結果であり、他の配線や指数については未検証である。
- 実行時間とメモリの値は上記の限定した入力、算術領域、実装、機材に対するものである。論文全体の独立証明検証、固定版Leanのローカルビルド、非ゼロ例外を伴う完全な共有テンプレート、節約条件を満たす再帰、一般長への展開は未完了である。 [探索範囲・停止理由・否定的結果](RECORD_SEARCH.md) · [生データ](../results/record-search.json)

## 8. 今回の達成事項と再開条件

既知の成果の再現は、固定版プレプリントの範囲を限定した構成の実装と検証、および既知の小規模 Walsh 回路の厳密な再実行と展開である。このリポジトリ固有の成果は、固定テンプレートの独立した実装と検証、疎ルーティングとペンシル縮小のアブレーション、端点窓とシフト削減の計数、比較条件を明記した測定、範囲を固定した探索の記録である。

研究を再開する場合は、次のいずれかを満たす具体的な候補と、時間・メモリの上限を先に定める。

1. 独立入力と例外修復の正当性を保ちつつ、シフト数または明示的なアドレス領域を構造的に減らし、厳密な軸変換呼び出し数の節約を示せる候補。
2. H16の53算術演算、H8の18ゲートまたはスケール付き19算術演算のいずれかを目指す、今回の探索範囲を超える具体的な配線変更。公開比較値を更新した候補について、大規模展開やネイティブ実装の評価へ進む。

## 9. 再現、依存関係、ライセンス

Python 3.10以上とGitを使用する。パッケージ依存はNumPyとSciPy、開発用はpytest、研究用の任意依存はZ3である。通常CIはZ3を入れない構成で、SMTテストの `pytest.importorskip("z3")` がスキップを選ぶ。研究用CIの `research-z3` はZ3を導入し、対象テストが実際に実行され合格したことを確認する。 [依存定義](../pyproject.toml) · [CI定義](../.github/workflows/test.yml)

```sh
python -m venv .venv
# Activate the virtual environment before installing.
python -m pip install -e '.[dev,research]'
python -m pytest -q
python -m pytest -q tests/test_record_search.py::test_fixed_dag_scale_unsat_at_19
python -m nextfft_lab.bench --max-power 7 --repeats 2
```

実験ごとの全コマンド、依存の役割、測定環境と生データは別紙にまとめた。ベンチマークを再実行する場合は、保存済みの生データと回路を上書きしない出力先を選ぶ。 [再現手順と生データ索引](REPRODUCIBILITY.md)

| 実験 | コマンド | 保存先・測定方法 |
|---|---|---|
| 予測、ペンシル、固定テンプレート | `python -m nextfft_lab.bench_repair --repeats 20`<br>`python -m nextfft_lab.bench_pencil --repeats 20`<br>`python -m nextfft_lab.bench_kernel --repeats 20 --template-repeats 3` | [初期検証記録](ROADMAP.md) |
| 最適化の比較 | `python -m nextfft_lab.bench_optimization --variant compact --repeats 3`。同じ条件で `baseline`、`routing-only`、`classical` を実行する。 | [実行手順と生データへの索引](OPTIMIZATION.md) |
| 小規模回路・既知回路展開 | `python -m nextfft_lab.bench_circuit --repeats 20` | [回路と実測データ](CIRCUIT_RESEARCH.md) |
| 公開記録近傍の探索 | `python -m nextfft_lab.bench_record_search --reference-repo ../published-wht-reference` | [上流Gitツリーの準備、探索上限、生データ](RECORD_SEARCH.md) |

独自のコードと文書はMITで公開する。SussmanのH8に由来するスケール付き回路データはApache-2.0の帰属とライセンスを同梱する。原論文、参考文献、依存パッケージは各権利者・配布元の条件に従う。 [MITライセンス](../LICENSE) · [回路の帰属](../results/record-circuits/NOTICE.md) · [Apache-2.0ライセンス](../results/record-circuits/LICENSE-APACHE-2.0.txt)

## 10. 公開準備と承認後の手順

完成処理では CPython 3.13.3 と固定版 Z3 で172件がすべて合格し、JUnit の試験記録でも対象SMTテストの実行と合格を確認した。古典ベンチマークのスモーク実行と依存関係の検査にも合格した。ローカルで作成した v0.1.0 wheel の版番号、研究用依存、MITライセンス同梱とパッケージ内容を検査した。

PR #1は固定テンプレートと最適化、PR #2はPR #1を土台とした回路探索と公開準備を含む。承認後はPR #1を先に履歴が残る方式でマージし、PR #2の向き先を `main` に変更して差分とCIを再確認する。PR #2の取り込み後に `main` の確定コミットから v0.1.0 Research Preview を作成する。マージ、リリースタグおよび公開は承認事項とする。 [PR #1](https://github.com/so-s1m0n/NextFFTlab/pull/1) · [PR #2](https://github.com/so-s1m0n/NextFFTlab/pull/2)
