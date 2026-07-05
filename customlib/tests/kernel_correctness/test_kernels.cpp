#include "../../kernels/kernels.hpp"

#include <cassert>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
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
    const int cols = 24;
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

std::vector<float> stableSoftmax(const std::vector<float>& x) {
    const float max_value = *std::max_element(x.begin(), x.end());
    std::vector<float> out(x.size());
    float denom = 0.0f;
    for (size_t i = 0; i < x.size(); ++i) {
        out[i] = std::exp(x[i] - max_value);
        denom += out[i];
    }
    for (float& v : out) {
        v /= denom;
    }
    return out;
}

void testStableSoftmax() {
    const std::vector<float> x = {1000.0f, 1001.0f, 999.0f, -1000.0f};
    const std::vector<float> got = stableSoftmax(x);
    const float denom = 1.0f + std::exp(-1.0f) + std::exp(-2.0f) + std::exp(-2001.0f);
    requireClose(got[1], 1.0f / denom, 1.0e-6f, "softmax");
    float sum = 0.0f;
    for (float v : got) {
        assert(std::isfinite(v));
        sum += v;
    }
    requireClose(sum, 1.0f, 1.0e-6f, "softmax_sum");
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

void testAttentionAgainstScalarReference() {
    const int context = 4;
    const int kv_heads = 2;
    const int q_heads = 4;
    const int dim = 3;
    std::vector<float> q(q_heads * dim);
    std::vector<float> k(context * kv_heads * dim);
    std::vector<float> v(context * kv_heads * dim);
    for (size_t i = 0; i < q.size(); ++i) {
        q[i] = std::sin(static_cast<float>(i + 1) * 0.13f);
    }
    for (size_t i = 0; i < k.size(); ++i) {
        k[i] = std::cos(static_cast<float>(i + 2) * 0.17f);
        v[i] = std::sin(static_cast<float>(i + 3) * 0.07f);
    }
    std::vector<float> got(q_heads * dim, 0.0f);
    xq::kernels::attentionDecodeReference(q.data(), k.data(), v.data(), context, kv_heads, q_heads, dim, got.data());

    const int group = q_heads / kv_heads;
    for (int qh = 0; qh < q_heads; ++qh) {
        const int kh = qh / group;
        std::vector<float> scores(static_cast<size_t>(context));
        for (int t = 0; t < context; ++t) {
            float dot = 0.0f;
            for (int d = 0; d < dim; ++d) {
                dot += q[static_cast<size_t>(qh * dim + d)] *
                       k[static_cast<size_t>((t * kv_heads + kh) * dim + d)];
            }
            scores[static_cast<size_t>(t)] = dot / std::sqrt(static_cast<float>(dim));
        }
        const std::vector<float> probs = stableSoftmax(scores);
        for (int d = 0; d < dim; ++d) {
            float expected = 0.0f;
            for (int t = 0; t < context; ++t) {
                expected += probs[static_cast<size_t>(t)] *
                            v[static_cast<size_t>((t * kv_heads + kh) * dim + d)];
            }
            requireClose(got[static_cast<size_t>(qh * dim + d)], expected, 1.0e-5f, "attention_scalar");
        }
    }
}

void testKvCacheAppendRead() {
    const int context = 3;
    const int kv_heads = 2;
    const int dim = 4;
    std::vector<float> cache;
    for (int t = 0; t < context; ++t) {
        for (int h = 0; h < kv_heads; ++h) {
            for (int d = 0; d < dim; ++d) {
                cache.push_back(static_cast<float>(100 * t + 10 * h + d));
            }
        }
    }
    const float* row = cache.data() + (static_cast<size_t>(2) * kv_heads + 1) * dim;
    requireClose(row[3], 213.0f, 0.0f, "kv_cache");
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

void testLmHeadArgmaxAndGreedySampling() {
    const int vocab = 4;
    const int hidden = 4;
    const float logits[vocab] = {-1.0f, 0.5f, 2.0f, 1.9f};
    int best = 0;
    for (int i = 1; i < vocab; ++i) {
        if (logits[i] > logits[best]) {
            best = i;
        }
    }
    assert(best == 2);

    const std::vector<float> h = {0.25f, -0.5f, 2.0f, 0.125f};
    const std::vector<float> w = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.5f, 0.5f, 0.5f, 0.5f,
    };
    int projected_best = 0;
    float projected_value = -std::numeric_limits<float>::infinity();
    for (int r = 0; r < vocab; ++r) {
        float acc = 0.0f;
        for (int c = 0; c < hidden; ++c) {
            acc += w[static_cast<size_t>(r * hidden + c)] * h[static_cast<size_t>(c)];
        }
        if (acc > projected_value) {
            projected_value = acc;
            projected_best = r;
        }
    }
    assert(projected_best == 2);

    auto q = xq::kernels::quantizeLowBit(w.data(), vocab, hidden, 4, 4);
    std::vector<float> dense;
    xq::kernels::dequantizeLowBitMatrix(q, &dense);
    int expected_best = 0;
    float expected_value = -std::numeric_limits<float>::infinity();
    for (int r = 0; r < vocab; ++r) {
        float acc = 0.0f;
        for (int c = 0; c < hidden; ++c) {
            acc += dense[static_cast<size_t>(r * hidden + c)] * h[static_cast<size_t>(c)];
        }
        if (acc > expected_value) {
            expected_value = acc;
            expected_best = r;
        }
    }
    float got_value = 0.0f;
    const int got_best = xq::kernels::gemvW4A16ArgmaxNeon(q, h.data(), &got_value);
    assert(got_best == expected_best);
    requireClose(got_value, expected_value, 1.0e-5f, "lm_head_argmax_w4");
}

}  // namespace

int main() {
    testGemv(4);
    testGemv(3);
    testGemv(2);
    testRmsNorm();
    testRope();
    testStableSoftmax();
    testAttention();
    testAttentionAgainstScalarReference();
    testKvCacheAppendRead();
    testDelta();
    testLmHeadArgmaxAndGreedySampling();
    std::cout << "kernel correctness passed\n";
    return 0;
}
