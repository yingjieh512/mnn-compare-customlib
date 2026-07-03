#include "../../kernels/kernels.hpp"

#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

namespace {

void requireClose(float a, float b, float tol, const char* what) {
    if (std::fabs(a - b) > tol) {
        std::cerr << what << " mismatch: " << a << " vs " << b << "\n";
        std::abort();
    }
}

void testGemv(int bits) {
    const int rows = 7;
    const int cols = 19;
    std::vector<float> w(rows * cols);
    std::vector<float> x(cols);
    for (int i = 0; i < rows * cols; ++i) {
        w[static_cast<size_t>(i)] = std::sin(static_cast<float>(i) * 0.17f) * 0.7f;
    }
    for (int i = 0; i < cols; ++i) {
        x[static_cast<size_t>(i)] = std::cos(static_cast<float>(i) * 0.11f);
    }
    auto q = xq::kernels::quantizeLowBit(w.data(), rows, cols, bits, 8);
    std::vector<float> dense;
    xq::kernels::dequantizeLowBitMatrix(q, &dense);
    std::vector<float> got(rows, 0.0f);
    if (bits == 4) {
        xq::kernels::gemvW4A16Neon(q, x.data(), got.data());
    } else if (bits == 3) {
        xq::kernels::gemvW3A16Neon(q, x.data(), got.data());
    } else {
        xq::kernels::gemvW2A16Neon(q, x.data(), got.data());
    }
    for (int r = 0; r < rows; ++r) {
        float expected = 0.0f;
        for (int c = 0; c < cols; ++c) {
            expected += dense[static_cast<size_t>(r * cols + c)] * x[static_cast<size_t>(c)];
        }
        requireClose(got[static_cast<size_t>(r)], expected, 1.0e-5f, "gemv");
    }
}

void testRmsNorm() {
    const int n = 16;
    std::vector<float> x(n), w(n), y(n);
    for (int i = 0; i < n; ++i) {
        x[static_cast<size_t>(i)] = 0.1f + static_cast<float>(i) * 0.03f;
        w[static_cast<size_t>(i)] = 1.0f + static_cast<float>(i) * 0.01f;
    }
    xq::kernels::rmsnormReference(x.data(), w.data(), n, 1.0e-6f, y.data());
    float sum = 0.0f;
    for (float v : x) {
        sum += v * v;
    }
    const float inv = 1.0f / std::sqrt(sum / n + 1.0e-6f);
    requireClose(y[3], x[3] * inv * w[3], 1.0e-6f, "rmsnorm");
}

void testRope() {
    std::vector<float> q = {1, 0, 0, 1};
    std::vector<float> k = {0, 1, 1, 0};
    xq::kernels::ropeReference(q.data(), k.data(), 1, 4, 7, 10000.0f);
    assert(std::isfinite(q[0]));
    assert(std::isfinite(k[0]));
}

void testAttention() {
    const int context = 3;
    const int kv_heads = 1;
    const int q_heads = 2;
    const int dim = 4;
    std::vector<float> q(q_heads * dim, 0.2f);
    std::vector<float> k(context * kv_heads * dim, 0.1f);
    std::vector<float> v(context * kv_heads * dim, 0.3f);
    std::vector<float> out(q_heads * dim, 0.0f);
    xq::kernels::attentionDecodeReference(q.data(), k.data(), v.data(), context, kv_heads, q_heads, dim, out.data());
    for (float value : out) {
        requireClose(value, 0.3f, 1.0e-5f, "attention");
    }
}

void testDelta() {
    const int kdim = 3;
    const int vdim = 2;
    float q[kdim] = {0.4f, 0.5f, 0.6f};
    float k[kdim] = {0.2f, 0.1f, 0.3f};
    float v[vdim] = {0.7f, -0.2f};
    std::vector<float> state(kdim * vdim, 0.0f);
    float out[vdim] = {0.0f, 0.0f};
    xq::kernels::gatedDeltaDecodeReference(q, k, v, 0.5f, -0.1f, kdim, vdim, state.data(), out);
    assert(std::isfinite(out[0]));
    assert(std::isfinite(out[1]));
}

}  // namespace

int main() {
    testGemv(4);
    testGemv(3);
    testGemv(2);
    testRmsNorm();
    testRope();
    testAttention();
    testDelta();
    std::cout << "kernel correctness passed\n";
    return 0;
}

