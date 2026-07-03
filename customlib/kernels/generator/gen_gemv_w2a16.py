#!/usr/bin/env python3
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
template = (ROOT / "generator" / "templates" / "gemv_lowbit.cpp.in").read_text()
out = template.replace("{{FUNC_NAME}}", "gemvW2A16Neon")
(ROOT / "generated" / "arm64_neon" / "xq_gemv_w2a16_neon.cpp").write_text(out)

