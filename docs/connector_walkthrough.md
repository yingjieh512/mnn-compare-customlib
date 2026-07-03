# Connector Walkthrough

The custom library uses MNN as the runtime substrate and keeps stock MNN unmodified for the baseline.

## MNN Version

Pinned MNN commit:

```text
0bff03cbef43c783f44e41484b9f8a0b28bd758d
```

The pinned tree includes Qwen3.5 export support:

- `transformers/llm/export/utils/model_mapper.py`
- `transformers/llm/export/utils/custom_op.py`
- `transformers/llm/export/utils/transformers.py`

MNN's exporter emits LLM custom op semantics such as:

- `LlmExporter::FakeLinear`
- `LlmExporter::FusedAttention`
- `LlmExporter::FusedLinearAttention`

## Rewrite Plan

`customlib/mnn_bridge/graph_rewrite.cpp` declares replacements:

- Quantized Linear -> `xqwen_linear_execution`
- RMSNorm -> `xqwen_rmsnorm_execution`
- RoPE -> `xqwen_rope_execution`
- GQA attention decode -> `xqwen_attention_execution`
- Gated Delta / Linear Attention -> `xqwen_delta_execution`
- FFN gate/up/SILU/mul/down -> `xqwen_ffn_execution`

The bridge prefers MNN Extra/custom op semantics. Schema patches should only be added under `patches/mnn` if a future MNN revision cannot represent the needed op.

## Fallback Rules

- Prefill may fall back to stock MNN when MNN is faster.
- Decode hot paths are replaced first.
- Any fallback must be logged in selected kernel metadata.
- The public ABI never exposes raw MNN objects.

