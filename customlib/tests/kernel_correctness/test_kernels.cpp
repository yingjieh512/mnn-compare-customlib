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

void testAffineAsymmetricGemv() {
    xq::kernels::QuantizedMatrix q;
    q.rows = 2;
    q.cols = 4;
    q.bits = 4;
    q.group_size = 4;
    q.affine_asymmetric = true;
    q.packed = {
        static_cast<uint8_t>((2u << 4) | 0u),
        static_cast<uint8_t>((15u << 4) | 7u),
        static_cast<uint8_t>((4u << 4) | 1u),
        static_cast<uint8_t>((8u << 4) | 6u),
    };
    q.scales = {0.5f, 0.25f};
    q.zeros = {-1.0f, 2.0f};
    const float x[4] = {1.0f, -2.0f, 0.5f, 3.0f};
    float y[2] = {};
    xq::kernels::gemvW4A16Neon(q, x, y);
    std::vector<float> dense;
    xq::kernels::dequantizeLowBitMatrix(q, &dense);
    for (int r = 0; r < q.rows; ++r) {
        float expected = 0.0f;
        for (int c = 0; c < q.cols; ++c) {
            expected += dense[static_cast<size_t>(r * q.cols + c)] * x[c];
        }
        requireClose(y[r], expected, 1.0e-6f, "affine_asymmetric_gemv");
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
    const int position = 7;
    const float theta = 10000.0f;
    xq::kernels::ropeReference(q.data(), k.data(), 1, 4, position, theta);
    const float c0 = std::cos(static_cast<float>(position));
    const float s0 = std::sin(static_cast<float>(position));
    const float inv1 = std::pow(theta, -0.5f);
    const float c1 = std::cos(static_cast<float>(position) * inv1);
    const float s1 = std::sin(static_cast<float>(position) * inv1);
    requireClose(q[0], c0, 1.0e-6f, "rope_q0");
    requireClose(q[2], s0, 1.0e-6f, "rope_q2");
    requireClose(q[1], -s1, 1.0e-6f, "rope_q1");
    requireClose(q[3], c1, 1.0e-6f, "rope_q3");
    requireClose(k[0], -s0, 1.0e-6f, "rope_k0");
    requireClose(k[2], c0, 1.0e-6f, "rope_k2");
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

float graphSoftplus(float x) {
    if (x > 20.0f) {
        return x;
    }
    return std::log1p(std::exp(x));
}

void testLinearAttentionMnnGraphInputs() {
    const int kdim = 3;
    const int vdim = 2;
    float q[kdim] = {0.4f, -0.5f, 0.6f};
    float k[kdim] = {0.2f, 0.1f, -0.3f};
    float v[vdim] = {0.7f, -0.2f};
    float q2[kdim] = {-0.25f, 0.35f, 0.45f};
    float k2[kdim] = {0.15f, -0.4f, 0.05f};
    float v2[vdim] = {-0.1f, 0.55f};

    auto l2Normalize = [](float* values, int n) {
        float sum = 0.0f;
        for (int i = 0; i < n; ++i) {
            sum += values[i] * values[i];
        }
        const float inv = 1.0f / std::sqrt(sum + 1.0e-6f);
        for (int i = 0; i < n; ++i) {
            values[i] *= inv;
        }
    };
    l2Normalize(q, kdim);
    l2Normalize(k, kdim);
    l2Normalize(q2, kdim);
    l2Normalize(k2, kdim);

    const float a_proj = -0.35f;
    const float a_proj2 = 0.125f;
    const float b_proj = 0.25f;
    const float b_proj2 = -0.45f;
    const float a_log = -2.65625f;
    const float dt_bias = -3.53125f;
    const float beta = 1.0f / (1.0f + std::exp(-b_proj));
    const float beta2 = 1.0f / (1.0f + std::exp(-b_proj2));
    const float gate = -std::exp(a_log) * graphSoftplus(a_proj + dt_bias);
    const float gate2 = -std::exp(a_log) * graphSoftplus(a_proj2 + dt_bias);

    std::vector<float> got_state(kdim * vdim, 0.0f);
    float got[vdim] = {0.0f, 0.0f};
    xq::kernels::gatedDeltaDecodeReference(q, k, v, beta, gate, kdim, vdim, got_state.data(), got);
    float got2[vdim] = {0.0f, 0.0f};
    xq::kernels::gatedDeltaDecodeReference(q2, k2, v2, beta2, gate2, kdim, vdim, got_state.data(), got2);

    std::vector<float> expected_state(kdim * vdim, 0.0f);
    float expected[vdim] = {0.0f, 0.0f};
    float expected2[vdim] = {0.0f, 0.0f};
    auto step = [&](const float* qv,
                    const float* kv,
                    const float* vv,
                    float beta_value,
                    float gate_value,
                    float* out) {
        const float decay = std::exp(gate_value);
        for (float& state_value : expected_state) {
            state_value *= decay;
        }
        float pred[vdim] = {0.0f, 0.0f};
        for (int kd = 0; kd < kdim; ++kd) {
            for (int vd = 0; vd < vdim; ++vd) {
                pred[vd] += expected_state[static_cast<size_t>(kd * vdim + vd)] * kv[kd];
            }
        }
        float delta[vdim] = {0.0f, 0.0f};
        for (int vd = 0; vd < vdim; ++vd) {
            delta[vd] = beta_value * (vv[vd] - pred[vd]);
        }
        for (int kd = 0; kd < kdim; ++kd) {
            for (int vd = 0; vd < vdim; ++vd) {
                expected_state[static_cast<size_t>(kd * vdim + vd)] += kv[kd] * delta[vd];
            }
        }
        for (int vd = 0; vd < vdim; ++vd) {
            out[vd] = 0.0f;
            for (int kd = 0; kd < kdim; ++kd) {
                out[vd] += qv[kd] * expected_state[static_cast<size_t>(kd * vdim + vd)];
            }
            out[vd] /= std::sqrt(static_cast<float>(kdim));
        }
    };
    step(q, k, v, beta, gate, expected);
    step(q2, k2, v2, beta2, gate2, expected2);

    for (int i = 0; i < kdim * vdim; ++i) {
        requireClose(got_state[static_cast<size_t>(i)],
                     expected_state[static_cast<size_t>(i)],
                     1.0e-6f,
                     "linear_attention_mnn_state");
    }
    for (int i = 0; i < vdim; ++i) {
        requireClose(got[i], expected[i], 1.0e-6f, "linear_attention_mnn_out_step1");
        requireClose(got2[i], expected2[i], 1.0e-6f, "linear_attention_mnn_out_step2");
    }
}

void testQwen35PerHeadQGateSplit() {
    const int heads = 3;
    const int head_dim = 4;
    const int gated_head_dim = head_dim * 2;
    std::vector<float> fused(static_cast<size_t>(heads * gated_head_dim));
    for (int h = 0; h < heads; ++h) {
        for (int d = 0; d < head_dim; ++d) {
            fused[static_cast<size_t>(h * gated_head_dim + d)] = 100.0f * h + static_cast<float>(d);
            fused[static_cast<size_t>(h * gated_head_dim + head_dim + d)] =
                1000.0f + 100.0f * h + static_cast<float>(d);
        }
    }
    std::vector<float> query(static_cast<size_t>(heads * head_dim));
    std::vector<float> gate(static_cast<size_t>(heads * head_dim));
    for (int h = 0; h < heads; ++h) {
        const float* src = fused.data() + static_cast<size_t>(h * gated_head_dim);
        std::copy(src, src + head_dim, query.data() + static_cast<size_t>(h * head_dim));
        std::copy(src + head_dim, src + gated_head_dim, gate.data() + static_cast<size_t>(h * head_dim));
    }
    requireClose(query[static_cast<size_t>(head_dim)], 100.0f, 0.0f, "qgate_query_head1");
    requireClose(gate[static_cast<size_t>(head_dim)], 1100.0f, 0.0f, "qgate_gate_head1");
    requireClose(query[static_cast<size_t>(2 * head_dim + 3)], 203.0f, 0.0f, "qgate_query_head2");
    requireClose(gate[static_cast<size_t>(2 * head_dim + 3)], 1203.0f, 0.0f, "qgate_gate_head2");
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
    testAffineAsymmetricGemv();
    testRmsNorm();
    testRope();
    testStableSoftmax();
    testAttention();
    testAttentionAgainstScalarReference();
    testKvCacheAppendRead();
    testDelta();
    testLinearAttentionMnnGraphInputs();
    testQwen35PerHeadQGateSplit();
    testLmHeadArgmaxAndGreedySampling();
    std::cout << "kernel correctness passed\n";
    return 0;
}
