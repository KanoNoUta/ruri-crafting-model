# RURI-Craft G1 · 琉璃第一代生产模型

面向 FFXIV 八个生产职业的轻量策略模型：根据制作属性、配方、当前状态与合法技能，
预测下一技能、目标价值和剩余技能次数。**第一代编号：`RURI-Craft-G1`；版本：`v1.0.0-beta.1`。**

[下载 ONNX / 权重](https://github.com/KanoNoUta/ruri-crafting-model/releases/tag/v1.0.0-beta.1) ·
[开源训练框架](https://github.com/KanoNoUta/ruri-crafting-framework) ·
[模型说明](MODEL_CARD.md) · [接口元数据](metadata.json) · [版本索引](modelmaster.json)

**451,404 参数 · ONNX 1.815 MB · CPU 离线推理 · Apache-2.0**

G1 的主要价值是快速提供技能候选，适合作为混合求解的模型分支。
本页同时报告与本地传统搜索器的对照，以及与旧神经网络的训练改进，两个基准分开解读。

## 速度：相同状态下的候选响应开销

在 Ryzen 7 7800X3D 上，对 **24 个相同保存状态**进行对照：

| 指标 | 本地传统搜索 | RURI-Craft G1 |
| --- | ---: | ---: |
| 相同起点的单次决策中位耗时 | 193.009 ms | **0.1701 ms** |
| 此样本集两组中位数之比 | 约 1,135 倍 | 候选响应开销更低 |
| 工作内容 | 搜索后返回下一技能，可能无解 | 编码、合法掩码、ONNX、选技能 |

![同一状态下的模型与传统搜索决策耗时](assets/decision-latency.png)

比较对象为本框架的 **GlobalParetoSearch（普通）/ DeterministicBeamSearch（专家）**，
每步采用 1 秒、60,000 节点预算；关闭宏缓存。模型使用 CPUExecutionProvider 单线程。
计时排除加载、进程通信和规则模拟；模型每起点预热后测 30 次，搜索每起点测 1 次。
表中取每个起点的响应时间，再对 24 个起点取中位数。
普通的单步收尾状态中，搜索也可能更快；图中展示全部起点。

**这不是上游 Raphael 对比，不是 128 核教师生成对比，也不是完整制作快 1,135 倍。**
技能动画、执行等待和实际技能次数未包含在响应耗时里。传统搜索还承担了模型预测不具备的搜索工作。

## 精度：比上一版神经网络学得更准

在同一份 **44,450 条历史留出状态**中：

| 指标 | 旧神经网络基线 | G1 | 变化 |
| --- | ---: | ---: | ---: |
| 整体下一技能一致率 | 84.36% | **92.01%** | **+7.65 个百分点** |
| 普通配方一致率，41,720 条 | 84.98% | 92.79% | +7.81 个百分点 |
| 严格专家标签一致率，2,339 条 | 73.02% | 78.97% | +5.94 个百分点 |
| 宇宙概率标签一致率，391 条 | 85.42% | 86.70% | +1.28 个百分点 |
| 整体前三技能覆盖率 | 97.95% | 98.68% | +0.73 个百分点 |
| 剩余技能次数预测 MAE | 0.677 次 | **0.573 次** | **误差降低 15.39%** |

![与旧神经网络基线的技能一致率对比](assets/agreement.png)

“一致率”表示与教师下一技能标签相同，不等于制作成功率，也不是比传统算法更准确的证据。
历史留出集已重复使用，专家分支方案曾受到其中回退诊断的启发，所以这不是新的独立盲测。
宇宙概率子集的 Top-3 从 99.49% 降到 98.72%，也保留在原始报告中。

## 实际技能次数与模拟达标：尚未全面超过传统搜索

同一套规则模拟器中，从每类 8 个保存状态继续制作，每状态使用 2 个相同随机种子；
两种方法每步都读取实际模拟结果重新决策。每方法共 48 条续作轨迹：

| 分组 | 本地传统搜索达标 | G1 达标 |
| --- | ---: | ---: |
| 普通状态 | 16 / 16 | 15 / 16 |
| 严格专家标签状态 | 16 / 16 | 15 / 16 |
| 宇宙概率标签状态 | 0 / 16 | 2 / 16 |
| 合计（分层等权） | **32 / 48** | **32 / 48** |

![同一模拟器下的续作达标对比](assets/continuation.png)

达标要求完成进度且满足原品质目标，失败、无建议和耗尽步数都留在分母中。
在两种方法**共同达标的 30 条配对轨迹**中，剩余实际技能次数中位数为搜索 **3 次**、模型 **4 次**。
因此目前不能宣称 G1 已减少实际技能次数或达到最短路径。

这是少量历史中间状态的模拟续作测试，不是从零制作全游戏配方的成功率，也不是游戏客户端实测。
每状态的两个种子存在共享起点，不能算成两个独立配方。宇宙高难总体仍有明显短板。
本次对照不启用模型失败后的算法回退；它不代表尚未完成接入的混合系统最终效果。

## 效率与代价

两种方法完成各自 48 条续作轨迹的累计决策计算时间：搜索约 **28.191 秒**，G1 约 **0.127 秒**。
两者访问的中间状态、停止位置和动作数不同，这只是本次运行的资源记录，不能据此推算同等工作量吞吐、能耗或租机费用。

![预测误差、推理耗时与模型体积的权衡](assets/tradeoffs.png)

相对旧单网络，G1 用双分支换取更好的技能一致率：历史同机 ONNX 中位延迟从
0.0510 ms 增至 0.0964 ms，文件从 0.907 MB 增至 1.815 MB。
这组历史数据只测预编码后的 ONNX，不能与本次 7800X3D 的完整决策时间混算。

## 下载与使用

Release 包含 `ruri-craft-g1.onnx`、`ruri-craft-g1.weights.pt`、`metadata.json`、
`SHA256SUMS` 和便于一次下载的 ZIP。ONNX 和 PyTorch 权重都不需要 GPU 才能使用。

```sh
python -m pip install numpy==1.26.4 onnxruntime==1.20.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
# 将 Release 文件放到 artifacts/ 后，在本仓库根目录运行：
python examples/predict.py --model artifacts/ruri-craft-g1.onnx --metadata metadata.json --input examples/example-input.json
```

示例输入是离线数值状态。自己的调用方必须按元数据排列 106 维 float32 特征，并提供准确的
36 维布尔合法掩码；空掩码应停止。标准化已经嵌入模型，不能重复标准化。
`value` 尚未完成失败状态概率校准，不能作为安全放行条件。
权重恢复与微调说明见[框架文档](https://github.com/KanoNoUta/ruri-crafting-framework/blob/v0.1.0/docs/TRAINING.md)。

当前是研究测试版，**尚未集成或发布到插件**。推荐后续使用规则检查、模拟验证和传统算法回退。
留存的新教师数据尚未加入这一代模型。

## 证据与复现

- [旧模型评估](evidence/baseline-holdout.json)、[G1 评估](evidence/g1-holdout.json)、[历史配对对比](evidence/paired-comparison.json)
- [同机续作原始结果](evidence/continuation-benchmark.json)、[发布校验](evidence/release-validation.json)
- [固定基准输入](https://github.com/KanoNoUta/ruri-crafting-framework/blob/v0.1.0/benchmarks/g1-cases.jsonl)、[基准脚本](https://github.com/KanoNoUta/ruri-crafting-framework/blob/v0.1.0/scripts/benchmark_model.py)
- [图表生成脚本](scripts/render_charts.py)、[评估口径](docs/BENCHMARKS.md)、[许可](LICENSE)

生成图表：安装 Matplotlib 3.9.4 后运行 `python scripts/render_charts.py`。中文字体使用微软雅黑或 Noto Sans CJK SC。
