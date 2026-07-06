#ifndef XQWEN35_KERNELS_KERNELS_HPP_
#define XQWEN35_KERNELS_KERNELS_HPP_

#include <cstdint>
#include <string>
#include <vector>

namespace xq {
namespace kernels {

struct QuantizedMatrix {
    int rows = 0;
    int cols = 0;
    int bits = 4;
    int group_size = 64;
    bool affine_asymmetric = false;
    std::vector<uint8_t> packed;
    std::vector<float> scales;
    std::vector<float> zeros;
    std::vector<float> bias;
};

QuantizedMatrix quantizeLowBit(const float* weights, int rows, int cols, int bits, int group_size);
float dequantizeValue(const QuantizedMatrix& matrix, int row, int col);
void dequantizeLowBitMatrix(const QuantizedMatrix& matrix, std::vector<float>* out);
void gemvLowBitReference(const QuantizedMatrix& matrix, const float* x, float* y);
void gemvW4A16Neon(const QuantizedMatrix& matrix, const float* x, float* y);
int gemvW4A16ArgmaxNeon(const QuantizedMatrix& matrix, const float* x, float* out_value);
void gemvW3A16Neon(const QuantizedMatrix& matrix, const float* x, float* y);
void gemvW2A16Neon(const QuantizedMatrix& matrix, const float* x, float* y);

void rmsnormReference(const float* x, const float* weight, int n, float eps, float* y);
void ropeReference(float* q, float* k, int heads, int head_dim, int position, float theta);
void attentionDecodeReference(const float* q,
                              const float* k_cache,
                              const float* v_cache,
                              int context,
                              int kv_heads,
                              int q_heads,
                              int head_dim,
                              float* out);
void gatedDeltaDecodeReference(const float* q,
                               const float* k,
                               const float* v,
                               float beta,
                               float gate,
                               int key_dim,
                               int value_dim,
                               float* state,
                               float* out);

std::string detectCpuFeatures();
std::string selectKernelSummary(int quant_bits);

}  // namespace kernels
}  // namespace xq

#endif  // XQWEN35_KERNELS_KERNELS_HPP_
