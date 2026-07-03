# Qwen3.5-9B Model Facts

Source: `Qwen/Qwen3.5-9B` at revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, read from `config.json`.

```json
{
  "model_type": "qwen3_5_text",
  "hidden_size": 4096,
  "head_dim": 256,
  "num_attention_heads": 16,
  "num_key_value_heads": 4,
  "num_hidden_layers": 32,
  "vocab_size": 248320,
  "intermediate_size": 12288,
  "max_position_embeddings": 262144,
  "rms_norm_eps": 1e-06,
  "linear_key_head_dim": 128,
  "linear_value_head_dim": 128,
  "linear_num_key_heads": 16,
  "linear_num_value_heads": 32,
  "linear_conv_kernel_dim": 4,
  "full_attention_interval": 4,
  "layer_types_len": 32,
  "layer_types_pattern": "linear_attention, linear_attention, linear_attention, full_attention, repeated"
}
```

The model has hybrid layers with linear attention/Gated Delta and full attention. Kernel generation must use these config values, not hardcoded assumptions.

