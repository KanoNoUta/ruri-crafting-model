# RURI-Craft G1 · v1.0.0-beta.1

本包包含第一代生产模型、PyTorch 权重、接口元数据和离线调用示例。

```sh
python -m pip install numpy==1.26.4 onnxruntime==1.20.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
python examples/predict.py --model ruri-craft-g1.onnx --metadata metadata.json --input examples/example-input.json
```

请保持 106 维特征和 36 个动作掩码的顺序与 metadata.json 一致。
标准化已嵌入 ONNX，空合法掩码应停止；value 不是已校准的成功概率。
SHA256SUMS 用于验证本包的模型、权重和元数据。

完整说明、图表与原始证据：https://github.com/KanoNoUta/ruri-crafting-model

训练框架：https://github.com/KanoNoUta/ruri-crafting-framework

本版是实验模型，尚未接入插件；低候选响应开销不代表全局最短制作或更高达标率。
精简权重可供研究初始化，不包含原优化器。代码说明与权重使用 Apache-2.0。
