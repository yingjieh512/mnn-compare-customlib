#include "../kernels.hpp"

#include <algorithm>
#include <cmath>

namespace xq {
namespace kernels {
namespace {

uint32_t readBits(const std::vector<uint8_t>& bytes, size_t bit_offset, int bits) {
    uint32_t v = 0;
    for (int i = 0; i < bits; ++i) {
        const size_t p = bit_offset + static_cast<size_t>(i);
        const uint8_t bit = static_cast<uint8_t>((bytes[p >> 3] >> (p & 7)) & 1u);
        v |= static_cast<uint32_t>(bit) << i;
    }
    return v;
}

void writeBits(std::vector<uint8_t>* bytes, size_t bit_offset, int bits, uint32_t value) {
    for (int i = 0; i < bits; ++i) {
        const size_t p = bit_offset + static_cast<size_t>(i);
        const uint8_t mask = static_cast<uint8_t>(1u << (p & 7));
        if ((value >> i) & 1u) {
            (*bytes)[p >> 3] = static_cast<uint8_t>((*bytes)[p >> 3] | mask);
        } else {
            (*bytes)[p >> 3] = static_cast<uint8_t>((*bytes)[p >> 3] & ~mask);
        }
    }
}

int groupsPerRow(int cols, int group_size) {
    return (cols + group_size - 1) / group_size;
}

}  // namespace

QuantizedMatrix quantizeLowBit(const float* weights, int rows, int cols, int bits, int group_size) {
    QuantizedMatrix q;
    q.rows = rows;
    q.cols = cols;
    q.bits = bits;
    q.group_size = group_size;
    const int qmax = (1 << bits) - 1;
    const int gpr = groupsPerRow(cols, group_size);
    q.scales.assign(static_cast<size_t>(rows * gpr), 1.0f);
    q.zeros.assign(static_cast<size_t>(rows * gpr), 0.0f);
    q.bias.assign(static_cast<size_t>(rows), 0.0f);
    q.packed.assign((static_cast<size_t>(rows) * cols * bits + 7) / 8, 0);

    for (int r = 0; r < rows; ++r) {
        for (int g = 0; g < gpr; ++g) {
            const int c0 = g * group_size;
            const int c1 = std::min(cols, c0 + group_size);
            float mn = weights[r * cols + c0];
            float mx = mn;
            for (int c = c0; c < c1; ++c) {
                mn = std::min(mn, weights[r * cols + c]);
                mx = std::max(mx, weights[r * cols + c]);
            }
            const float scale = (mx > mn) ? ((mx - mn) / static_cast<float>(qmax)) : 1.0f;
            const float zero = (mx > mn) ? std::round(-mn / scale) : 0.0f;
            q.scales[static_cast<size_t>(r * gpr + g)] = scale;
            q.zeros[static_cast<size_t>(r * gpr + g)] = zero;
            for (int c = c0; c < c1; ++c) {
                float normalized = weights[r * cols + c] / scale + zero;
                int code = static_cast<int>(std::round(normalized));
                code = std::max(0, std::min(qmax, code));
                const size_t bit_offset = (static_cast<size_t>(r) * cols + c) * bits;
                writeBits(&q.packed, bit_offset, bits, static_cast<uint32_t>(code));
            }
        }
    }
    return q;
}

float dequantizeValue(const QuantizedMatrix& matrix, int row, int col) {
    const int gpr = groupsPerRow(matrix.cols, matrix.group_size);
    const int group = col / matrix.group_size;
    const size_t bit_offset = (static_cast<size_t>(row) * matrix.cols + col) * matrix.bits;
    const uint32_t code = readBits(matrix.packed, bit_offset, matrix.bits);
    const size_t meta = static_cast<size_t>(row * gpr + group);
    return (static_cast<float>(code) - matrix.zeros[meta]) * matrix.scales[meta];
}

void dequantizeLowBitMatrix(const QuantizedMatrix& matrix, std::vector<float>* out) {
    out->assign(static_cast<size_t>(matrix.rows * matrix.cols), 0.0f);
    for (int r = 0; r < matrix.rows; ++r) {
        for (int c = 0; c < matrix.cols; ++c) {
            (*out)[static_cast<size_t>(r * matrix.cols + c)] = dequantizeValue(matrix, r, c);
        }
    }
}

void gemvLowBitReference(const QuantizedMatrix& matrix, const float* x, float* y) {
    for (int r = 0; r < matrix.rows; ++r) {
        float acc = matrix.bias.empty() ? 0.0f : matrix.bias[static_cast<size_t>(r)];
        for (int c = 0; c < matrix.cols; ++c) {
            acc += dequantizeValue(matrix, r, c) * x[c];
        }
        y[r] = acc;
    }
}

}  // namespace kernels
}  // namespace xq

