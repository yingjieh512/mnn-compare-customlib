#!/usr/bin/env python3
"""Numpy-only Qwen3.5 custom packer.

This packer avoids a PyTorch dependency so accuracy/debug passes can rebuild
XQ4 weights on a lean host. It reads safetensors payloads directly and can emit
MNN-style symmetric W4 block quantization for closer stock/custom comparison.
"""

import argparse
import json
import pathlib
import shutil
import struct
from typing import Dict, Iterable, List, Tuple

import numpy as np


PINNED_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
HF_REPO = "Qwen/Qwen3.5-9B"
MAGIC = b"XQW4A16\0"


def read_config(model_dir: pathlib.Path) -> Dict:
    data = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    return data.get("text_config", data)


def safe_name(name: str) -> str:
    return name.replace("model.language_model.", "").replace(".", "_")


def load_weight_map(model_dir: pathlib.Path) -> Dict[str, str]:
    index = json.loads((model_dir / "model.safetensors.index.json").read_text(encoding="utf-8"))
    return index["weight_map"]


def tensors_for_pack(config: Dict, limit_layers: int = 0) -> Tuple[List[str], List[str]]:
    n_layers = int(config["num_hidden_layers"])
    if limit_layers > 0:
        n_layers = min(n_layers, limit_layers)
    layer_types = config["layer_types"]
    matrix_names: List[str] = ["lm_head.weight"]
    vector_names: List[str] = ["model.language_model.norm.weight"]
    for layer in range(n_layers):
        prefix = f"model.language_model.layers.{layer}"
        vector_names.append(f"{prefix}.input_layernorm.weight")
        vector_names.append(f"{prefix}.post_attention_layernorm.weight")
        matrix_names.extend(
            [
                f"{prefix}.mlp.gate_proj.weight",
                f"{prefix}.mlp.up_proj.weight",
                f"{prefix}.mlp.down_proj.weight",
            ]
        )
        if layer_types[layer] == "full_attention":
            matrix_names.extend(
                [
                    f"{prefix}.self_attn.q_proj.weight",
                    f"{prefix}.self_attn.k_proj.weight",
                    f"{prefix}.self_attn.v_proj.weight",
                    f"{prefix}.self_attn.o_proj.weight",
                ]
            )
            vector_names.append(f"{prefix}.self_attn.q_norm.weight")
            vector_names.append(f"{prefix}.self_attn.k_norm.weight")
        else:
            matrix_names.extend(
                [
                    f"{prefix}.linear_attn.in_proj_qkv.weight",
                    f"{prefix}.linear_attn.in_proj_a.weight",
                    f"{prefix}.linear_attn.in_proj_b.weight",
                    f"{prefix}.linear_attn.in_proj_z.weight",
                    f"{prefix}.linear_attn.out_proj.weight",
                ]
            )
            vector_names.append(f"{prefix}.linear_attn.norm.weight")
            vector_names.append(f"{prefix}.linear_attn.conv1d.weight")
            vector_names.append(f"{prefix}.linear_attn.A_log")
            vector_names.append(f"{prefix}.linear_attn.dt_bias")
    return matrix_names, vector_names


def copy_small_files(model_dir: pathlib.Path, out_dir: pathlib.Path) -> None:
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"):
        src = model_dir / name
        if src.exists():
            shutil.copy2(src, out_dir / name)


class SafetensorStore:
    def __init__(self, model_dir: pathlib.Path, weight_map: Dict[str, str]):
        self.model_dir = model_dir
        self.weight_map = weight_map
        self.headers: Dict[str, Tuple[Dict, int]] = {}

    def _header(self, shard: str) -> Tuple[Dict, int]:
        if shard not in self.headers:
            path = self.model_dir / shard
            with path.open("rb") as f:
                header_len = struct.unpack("<Q", f.read(8))[0]
                header = json.loads(f.read(header_len).decode("utf-8"))
            self.headers[shard] = (header, 8 + int(header_len))
        return self.headers[shard]

    def meta(self, name: str) -> Tuple[str, List[int]]:
        shard = self.weight_map[name]
        header, _ = self._header(shard)
        item = header[name]
        return item["dtype"], [int(x) for x in item["shape"]]

    def read_tensor(self, name: str) -> np.ndarray:
        dtype, shape = self.meta(name)
        shard = self.weight_map[name]
        header, data_base = self._header(shard)
        item = header[name]
        elem_bytes = {"BF16": 2, "F16": 2, "F32": 4}[dtype]
        elements = int(np.prod(shape))
        start, _ = [int(x) for x in item["data_offsets"]]
        byte_count = elements * elem_bytes
        with (self.model_dir / shard).open("rb") as f:
            f.seek(data_base + start)
            raw = f.read(byte_count)
        if len(raw) != byte_count:
            raise IOError(f"{name}: short safetensors read")
        return self._decode_raw(raw, dtype).reshape(shape)

    def read_rows(self, name: str, row0: int, row_count: int) -> np.ndarray:
        shard = self.weight_map[name]
        header, data_base = self._header(shard)
        item = header[name]
        dtype = item["dtype"]
        shape = [int(x) for x in item["shape"]]
        if len(shape) == 1:
            cols = 1
            rows = shape[0]
        elif len(shape) == 2:
            rows, cols = shape
        else:
            raise ValueError(f"{name}: unsupported shape {shape}")
        if row0 < 0 or row_count < 0 or row0 + row_count > rows:
            raise ValueError(f"{name}: row slice out of range")
        elem_bytes = {"BF16": 2, "F16": 2, "F32": 4}[dtype]
        start, _ = [int(x) for x in item["data_offsets"]]
        byte_count = row_count * cols * elem_bytes
        byte_offset = data_base + start + row0 * cols * elem_bytes
        with (self.model_dir / shard).open("rb") as f:
            f.seek(byte_offset)
            raw = f.read(byte_count)
        if len(raw) != byte_count:
            raise IOError(f"{name}: short safetensors read")
        return self._decode_raw(raw, dtype).reshape(row_count, cols).copy()

    @staticmethod
    def _decode_raw(raw: bytes, dtype: str) -> np.ndarray:
        if dtype == "BF16":
            u16 = np.frombuffer(raw, dtype="<u2")
            arr = (u16.astype(np.uint32) << 16).view(np.float32)
        elif dtype == "F16":
            arr = np.frombuffer(raw, dtype="<f2").astype(np.float32)
        else:
            arr = np.frombuffer(raw, dtype="<f4").astype(np.float32, copy=False)
        return arr.copy()


def write_header(
    f,
    rows: int,
    cols: int,
    group_size: int,
    packed_bytes: int,
    meta_count: int,
    version: int = 1,
) -> None:
    f.write(
        struct.pack(
            "<8sIIIIIQQQ",
            MAGIC,
            version,
            rows,
            cols,
            group_size,
            4,
            int(packed_bytes),
            int(meta_count),
            int(meta_count),
        )
    )


def pack_matrix_w4(
    store: SafetensorStore,
    name: str,
    group_size: int,
    symmetric: bool,
    mnn_affine_asym: bool,
    mnn_alpha_fp16: bool,
    dst: pathlib.Path,
    chunk_rows: int,
) -> Dict:
    dtype, shape = store.meta(name)
    if len(shape) != 2:
        raise ValueError(f"{name}: matrix shape required, got {shape}")
    rows, cols = shape
    if cols % group_size != 0:
        raise ValueError(f"{name}: cols={cols} must be divisible by group_size={group_size}")
    groups = cols // group_size
    row_stride_bytes = cols // 2
    packed_bytes = rows * row_stride_bytes
    scales = np.empty((rows, groups), dtype=np.float32)
    zeros = np.empty((rows, groups), dtype=np.float32)
    with dst.open("wb") as f:
        write_header(f, rows, cols, group_size, packed_bytes, rows * groups, 2 if mnn_affine_asym else 1)
        for r0 in range(0, rows, chunk_rows):
            nr = min(chunk_rows, rows - r0)
            arr = store.read_rows(name, r0, nr)
            chunk = arr.reshape(nr, groups, group_size)
            if mnn_affine_asym:
                mn = chunk.min(axis=2)
                mx = chunk.max(axis=2)
                scale = ((mx - mn) / 15.0).astype(np.float32)
                scale = np.where(scale > 0.0, scale, 1.0).astype(np.float32)
                if mnn_alpha_fp16:
                    # MNN stores asymmetric alpha as fp16 [zero_bias, scale], where
                    # zero_bias = min - clip_min * scale = min + 8 * scale for W4.
                    # Runtime v2 consumes code * scale + min_eff, so reconstruct the
                    # effective min from the rounded fp16 alpha pair.
                    scale_f16 = scale.astype(np.float16).astype(np.float32)
                    zero_bias_f16 = (mn + 8.0 * scale).astype(np.float16).astype(np.float32)
                    scale = scale_f16
                    zero = (zero_bias_f16 - 8.0 * scale_f16).astype(np.float32)
                else:
                    zero = mn.astype(np.float32)
                codes = np.rint((chunk - zero[..., None]) / scale[..., None]).clip(0, 15).astype(np.uint8)
            elif symmetric:
                absmax = np.max(np.abs(chunk), axis=2)
                scale = (absmax / 7.0).astype(np.float32)
                scale = np.where(scale > 0.0, scale, 1.0).astype(np.float32)
                zero = np.full_like(scale, 8.0, dtype=np.float32)
                codes = np.rint(chunk / scale[..., None] + 8.0).clip(0, 15).astype(np.uint8)
            else:
                mn = chunk.min(axis=2)
                mx = chunk.max(axis=2)
                scale = ((mx - mn) / 15.0).astype(np.float32)
                scale = np.where(scale > 0.0, scale, 1.0).astype(np.float32)
                zero = np.rint(-mn / scale).clip(0.0, 15.0).astype(np.float32)
                codes = np.rint(chunk / scale[..., None] + zero[..., None]).clip(0, 15).astype(np.uint8)
            pair = codes[:, :, 0::2] | (codes[:, :, 1::2] << 4)
            f.write(pair.reshape(nr, -1).tobytes(order="C"))
            scales[r0 : r0 + nr] = scale
            zeros[r0 : r0 + nr] = zero
        f.write(scales.tobytes(order="C"))
        f.write(zeros.tobytes(order="C"))
    return {
        "file": dst.name,
        "rows": rows,
        "cols": cols,
        "bits": 4,
        "group_size": group_size,
        "format_version": 2 if mnn_affine_asym else 1,
        "symmetric": bool(symmetric),
        "mnn_affine_asymmetric": bool(mnn_affine_asym),
        "mnn_alpha_fp16": bool(mnn_alpha_fp16),
        "packed_bytes": int(packed_bytes),
        "scale_count": int(scales.size),
        "zero_count": int(zeros.size),
        "source_dtype": dtype,
    }


def write_vector_f32(store: SafetensorStore, name: str, dst: pathlib.Path) -> Dict:
    arr = store.read_tensor(name).astype(np.float32, copy=False).reshape(-1)
    with dst.open("wb") as f:
        f.write(arr.tobytes(order="C"))
    return {"file": dst.name, "elements": int(arr.size), "dtype": "float32"}


def pack_tensors(
    store: SafetensorStore,
    out_dir: pathlib.Path,
    names: Iterable[str],
    group_size: int,
    symmetric: bool,
    mnn_affine_asym: bool,
    mnn_alpha_fp16: bool,
    chunk_rows: int,
) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for i, name in enumerate(names, 1):
        dst = out_dir / f"{safe_name(name)}.xq4"
        print(
            f"[{i}] pack {name} -> {dst.name} group={group_size} "
            f"symmetric={symmetric} mnn_affine_asym={mnn_affine_asym} mnn_alpha_fp16={mnn_alpha_fp16}",
            flush=True,
        )
        out[name] = pack_matrix_w4(
            store, name, group_size, symmetric, mnn_affine_asym, mnn_alpha_fp16, dst, chunk_rows
        )
    return out


def pack_vectors(store: SafetensorStore, out_dir: pathlib.Path, names: Iterable[str]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for name in names:
        if name not in store.weight_map:
            continue
        dst = out_dir / f"{safe_name(name)}.f32"
        print(f"pack {name} -> {dst.name}", flush=True)
        out[name] = write_vector_f32(store, name, dst)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--group-size", type=int, default=128)
    parser.add_argument("--symmetric", action="store_true", help="Use MNN-style signed symmetric W4 codes.")
    parser.add_argument(
        "--mnn-affine-asym",
        action="store_true",
        help="Use MNN asymmetric W4 affine dequant: value = code * scale + min_bias.",
    )
    parser.add_argument(
        "--mnn-alpha-fp16",
        action="store_true",
        help="Round MNN asymmetric alpha metadata through fp16 before writing XQ4 float32 metadata.",
    )
    parser.add_argument(
        "--only-matrix",
        action="append",
        default=[],
        help="Pack only the named 2-D matrix tensor; may be passed multiple times.",
    )
    parser.add_argument("--limit-layers", type=int, default=0)
    parser.add_argument("--copy-mnn-from", default="")
    parser.add_argument("--chunk-rows", type=int, default=256)
    args = parser.parse_args()

    model_dir = pathlib.Path(args.model_dir)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_small_files(model_dir, out_dir)
    if args.copy_mnn_from:
        src = pathlib.Path(args.copy_mnn_from)
        for name in ("llm.mnn", "llm.mnn.weight", "llm.mnn.json", "llm_config.json", "tokenizer.mtok", "embeddings_bf16.bin"):
            if (src / name).exists() and not (out_dir / name).exists():
                shutil.copy2(src / name, out_dir / name)

    config = read_config(model_dir)
    weight_map = load_weight_map(model_dir)
    store = SafetensorStore(model_dir, weight_map)
    matrix_names, vector_names = tensors_for_pack(config, args.limit_layers)
    if args.only_matrix:
        requested = set(args.only_matrix)
        missing = sorted(name for name in requested if name not in weight_map)
        if missing:
            raise ValueError(f"--only-matrix tensors not found: {missing}")
        matrix_names = [name for name in matrix_names if name in requested]
        vector_names = []
    if args.symmetric and args.mnn_affine_asym:
        raise ValueError("--symmetric and --mnn-affine-asym are mutually exclusive")
    if args.mnn_alpha_fp16 and not args.mnn_affine_asym:
        raise ValueError("--mnn-alpha-fp16 requires --mnn-affine-asym")
    matrices = pack_tensors(
        store,
        out_dir,
        matrix_names,
        args.group_size,
        args.symmetric,
        args.mnn_affine_asym,
        args.mnn_alpha_fp16,
        args.chunk_rows,
    )
    vectors = pack_vectors(store, out_dir, vector_names)
    if args.mnn_affine_asym:
        scheme = "w4a16_groupwise_mnn_affine_asymmetric"
    else:
        scheme = "w4a16_groupwise_symmetric" if args.symmetric else "w4a16_groupwise_asymmetric"
    manifest = {
        "hf_repo": HF_REPO,
        "hf_revision": PINNED_REVISION,
        "format": "xqwen35_custom_w4a16",
        "quantization": {
            "bits": 4,
            "group_size": args.group_size,
            "scheme": scheme,
            "mnn_style_symmetric": bool(args.symmetric),
            "mnn_affine_asymmetric": bool(args.mnn_affine_asym),
            "mnn_alpha_fp16": bool(args.mnn_alpha_fp16),
        },
        "hidden_size": int(config["hidden_size"]),
        "intermediate_size": int(config["intermediate_size"]),
        "num_hidden_layers": int(args.limit_layers or config["num_hidden_layers"]),
        "num_attention_heads": int(config["num_attention_heads"]),
        "num_key_value_heads": int(config["num_key_value_heads"]),
        "head_dim": int(config["head_dim"]),
        "linear_key_head_dim": int(config.get("linear_key_head_dim", 128)),
        "linear_value_head_dim": int(config.get("linear_value_head_dim", 128)),
        "linear_num_key_heads": int(config.get("linear_num_key_heads", 16)),
        "linear_num_value_heads": int(config.get("linear_num_value_heads", 32)),
        "linear_conv_kernel_dim": int(config.get("linear_conv_kernel_dim", 4)),
        "vocab_size": int(config["vocab_size"]),
        "layer_types": config["layer_types"][: int(args.limit_layers or config["num_hidden_layers"])],
        "rms_norm_eps": float(config["rms_norm_eps"]),
        "rope_theta": float(config["rope_parameters"]["rope_theta"]),
        "partial_rotary_factor": float(config["rope_parameters"].get("partial_rotary_factor", 1.0)),
        "matrices": matrices,
        "vectors": vectors,
    }
    (out_dir / "xqwen35_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "matrices": len(matrices), "vectors": len(vectors)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
