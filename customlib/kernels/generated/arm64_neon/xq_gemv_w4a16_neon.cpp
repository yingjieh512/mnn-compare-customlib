#include "../../kernels.hpp"

#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <functional>
#include <limits>
#include <mutex>
#include <thread>
#include <vector>

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>
#endif

namespace xq {
namespace kernels {
namespace {

int groupsPerRow(int cols, int group_size) {
    return (cols + group_size - 1) / group_size;
}

float sumGroupScalar(const float* x, int count) {
    float x_sum = 0.0f;
    for (int c = 0; c < count; ++c) {
        x_sum += x[c];
    }
    return x_sum;
}

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
float horizontalAdd(float32x4_t v) {
#if defined(__aarch64__)
    return vaddvq_f32(v);
#else
    const float32x2_t lo = vget_low_f32(v);
    const float32x2_t hi = vget_high_f32(v);
    const float32x2_t sum2 = vadd_f32(lo, hi);
    return vget_lane_f32(sum2, 0) + vget_lane_f32(sum2, 1);
#endif
}

float sumGroupNeon(const float* x, int count) {
    float32x4_t x_sum0 = vdupq_n_f32(0.0f);
    float32x4_t x_sum1 = vdupq_n_f32(0.0f);
    int c = 0;
    for (; c + 7 < count; c += 8) {
        x_sum0 = vaddq_f32(x_sum0, vld1q_f32(x + c));
        x_sum1 = vaddq_f32(x_sum1, vld1q_f32(x + c + 4));
    }
    float out = horizontalAdd(vaddq_f32(x_sum0, x_sum1));
    for (; c < count; ++c) {
        out += x[c];
    }
    return out;
}
#endif

float dotGroupW4CodesOnlyScalar(const uint8_t* packed, const float* x, int count) {
    float code_dot = 0.0f;
    for (int c = 0; c < count; c += 2) {
        const uint8_t byte = packed[c >> 1];
        code_dot += static_cast<float>(byte & 0x0fu) * x[c];
        if (c + 1 < count) {
            code_dot += static_cast<float>(byte >> 4) * x[c + 1];
        }
    }
    return code_dot;
}

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
float dotGroupW4CodesOnlyNeon(const uint8_t* packed, const float* x, int count) {
    float32x4_t code_dot0 = vdupq_n_f32(0.0f);
    float32x4_t code_dot1 = vdupq_n_f32(0.0f);
    int c = 0;
    for (; c + 15 < count; c += 16) {
        const uint8x8_t bytes = vld1_u8(packed + (c >> 1));
        const uint8x8_t lo = vand_u8(bytes, vdup_n_u8(0x0f));
        const uint8x8_t hi = vshr_n_u8(bytes, 4);
        const uint8x8x2_t interleaved = vzip_u8(lo, hi);

        const uint16x8_t codes01 = vmovl_u8(interleaved.val[0]);
        const uint16x8_t codes23 = vmovl_u8(interleaved.val[1]);
        const float32x4_t codes0 = vcvtq_f32_u32(vmovl_u16(vget_low_u16(codes01)));
        const float32x4_t codes1 = vcvtq_f32_u32(vmovl_u16(vget_high_u16(codes01)));
        const float32x4_t codes2 = vcvtq_f32_u32(vmovl_u16(vget_low_u16(codes23)));
        const float32x4_t codes3 = vcvtq_f32_u32(vmovl_u16(vget_high_u16(codes23)));

        code_dot0 = vmlaq_f32(code_dot0, codes0, vld1q_f32(x + c));
        code_dot1 = vmlaq_f32(code_dot1, codes1, vld1q_f32(x + c + 4));
        code_dot0 = vmlaq_f32(code_dot0, codes2, vld1q_f32(x + c + 8));
        code_dot1 = vmlaq_f32(code_dot1, codes3, vld1q_f32(x + c + 12));
    }
    return horizontalAdd(vaddq_f32(code_dot0, code_dot1)) +
           dotGroupW4CodesOnlyScalar(packed + (c >> 1), x + c, count - c);
}
#endif

float dotGroupW4CodesOnly(const uint8_t* packed, const float* x, int count) {
#if defined(__ARM_NEON) || defined(__ARM_NEON__)
    return dotGroupW4CodesOnlyNeon(packed, x, count);
#else
    return dotGroupW4CodesOnlyScalar(packed, x, count);
#endif
}

float sumGroup(const float* x, int count) {
#if defined(__ARM_NEON) || defined(__ARM_NEON__)
    return sumGroupNeon(x, count);
#else
    return sumGroupScalar(x, count);
#endif
}

class WorkerPool {
public:
    WorkerPool() {
        const unsigned hw = std::max(1u, std::thread::hardware_concurrency());
        const unsigned workers = std::min(8u, std::max(1u, hw));
        for (unsigned i = 1; i < workers; ++i) {
            workers_.emplace_back([this] { workerLoop(); });
        }
    }

    ~WorkerPool() {
        {
            std::lock_guard<std::mutex> lock(mu_);
            stop_ = true;
            generation_++;
        }
        cv_.notify_all();
        for (std::thread& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }
    }

    int threads() const {
        return static_cast<int>(workers_.size()) + 1;
    }

    template <typename Fn>
    void parallelFor(int begin, int end, int min_rows_per_thread, Fn&& fn) {
        const int count = end - begin;
        if (count <= 0) {
            return;
        }
        const int thread_count = std::min(threads(), std::max(1, (count + min_rows_per_thread - 1) / min_rows_per_thread));
        if (thread_count <= 1) {
            fn(begin, end);
            return;
        }

        std::atomic<int> next{begin};
        const int chunk = std::max(min_rows_per_thread, (count + thread_count * 4 - 1) / (thread_count * 4));
        std::function<void()> task = [&] {
            while (true) {
                const int r0 = next.fetch_add(chunk, std::memory_order_relaxed);
                if (r0 >= end) {
                    break;
                }
                fn(r0, std::min(end, r0 + chunk));
            }
        };

        {
            std::lock_guard<std::mutex> lock(mu_);
            active_task_ = &task;
            remaining_ = thread_count - 1;
            generation_++;
        }
        cv_.notify_all();
        task();

        std::unique_lock<std::mutex> lock(mu_);
        done_cv_.wait(lock, [&] { return remaining_ == 0; });
        active_task_ = nullptr;
        generation_++;
    }

private:
    void workerLoop() {
        uint64_t seen = 0;
        while (true) {
            std::function<void()>* task = nullptr;
            {
                std::unique_lock<std::mutex> lock(mu_);
                cv_.wait(lock, [&] { return stop_ || generation_ != seen; });
                if (stop_) {
                    return;
                }
                seen = generation_;
                task = active_task_;
            }
            if (task) {
                (*task)();
                std::lock_guard<std::mutex> lock(mu_);
                remaining_--;
                if (remaining_ == 0) {
                    done_cv_.notify_one();
                }
            }
        }
    }

    std::vector<std::thread> workers_;
    std::mutex mu_;
    std::condition_variable cv_;
    std::condition_variable done_cv_;
    std::function<void()>* active_task_ = nullptr;
    int remaining_ = 0;
    uint64_t generation_ = 0;
    bool stop_ = false;
};

WorkerPool& workerPool() {
    static WorkerPool* pool = new WorkerPool();
    return *pool;
}

void computeGroupSums(const QuantizedMatrix& matrix, const float* x, std::vector<float>* sums) {
    const int gpr = groupsPerRow(matrix.cols, matrix.group_size);
    sums->resize(static_cast<size_t>(gpr));
    for (int g = 0; g < gpr; ++g) {
        const int c0 = g * matrix.group_size;
        const int count = std::min(matrix.group_size, matrix.cols - c0);
        (*sums)[static_cast<size_t>(g)] = sumGroup(x + c0, count);
    }
}

float computeRow(const QuantizedMatrix& matrix,
                 const float* x,
                 const float* group_sums,
                 int gpr,
                 size_t row_stride_bytes,
                 int r) {
    float acc = matrix.bias.empty() ? 0.0f : matrix.bias[static_cast<size_t>(r)];
    for (int g = 0; g < gpr; ++g) {
        const int c0 = g * matrix.group_size;
        const int count = std::min(matrix.group_size, matrix.cols - c0);
        const size_t meta = static_cast<size_t>(r * gpr + g);
        const uint8_t* row_bytes = matrix.packed.data() + static_cast<size_t>(r) * row_stride_bytes + (c0 >> 1);
        const float code_dot = dotGroupW4CodesOnly(row_bytes, x + c0, count);
        acc += matrix.scales[meta] * (code_dot - matrix.zeros[meta] * group_sums[g]);
    }
    return acc;
}

}  // namespace

void gemvW4A16Neon(const QuantizedMatrix& matrix, const float* x, float* y) {
    if (matrix.bits != 4 || matrix.rows <= 0 || matrix.cols <= 0 || matrix.group_size <= 0) {
        if (matrix.rows > 0) {
            std::fill(y, y + matrix.rows, 0.0f);
        }
        return;
    }

    const int gpr = groupsPerRow(matrix.cols, matrix.group_size);
    const size_t row_stride_bytes = (static_cast<size_t>(matrix.cols) + 1u) / 2u;
    thread_local std::vector<float> group_sums;
    computeGroupSums(matrix, x, &group_sums);
    const float* sums = group_sums.data();

    auto compute_range = [&](int r0, int r1) {
        for (int r = r0; r < r1; ++r) {
            y[r] = computeRow(matrix, x, sums, gpr, row_stride_bytes, r);
        }
    };

    const int min_rows = matrix.cols >= 2048 ? 128 : 512;
    if (matrix.rows < min_rows * 2) {
        compute_range(0, matrix.rows);
    } else {
        workerPool().parallelFor(0, matrix.rows, min_rows, compute_range);
    }
}

int gemvW4A16ArgmaxNeon(const QuantizedMatrix& matrix, const float* x, float* out_value) {
    if (matrix.bits != 4 || matrix.rows <= 0 || matrix.cols <= 0 || matrix.group_size <= 0) {
        if (out_value) {
            *out_value = -std::numeric_limits<float>::infinity();
        }
        return 0;
    }

    const int gpr = groupsPerRow(matrix.cols, matrix.group_size);
    const size_t row_stride_bytes = (static_cast<size_t>(matrix.cols) + 1u) / 2u;
    thread_local std::vector<float> group_sums;
    computeGroupSums(matrix, x, &group_sums);
    const float* sums = group_sums.data();

    std::mutex best_mu;
    int global_best_index = 0;
    float global_best_value = -std::numeric_limits<float>::infinity();

    auto compute_range = [&](int r0, int r1) {
        int best_index = r0;
        float best_value = -std::numeric_limits<float>::infinity();
        for (int r = r0; r < r1; ++r) {
            const float value = computeRow(matrix, x, sums, gpr, row_stride_bytes, r);
            if (value > best_value || (value == best_value && r < best_index)) {
                best_value = value;
                best_index = r;
            }
        }
        std::lock_guard<std::mutex> lock(best_mu);
        if (best_value > global_best_value || (best_value == global_best_value && best_index < global_best_index)) {
            global_best_value = best_value;
            global_best_index = best_index;
        }
    };

    if (matrix.rows < 8192) {
        compute_range(0, matrix.rows);
    } else {
        workerPool().parallelFor(0, matrix.rows, 4096, compute_range);
    }

    if (out_value) {
        *out_value = global_best_value;
    }
    return global_best_index;
}

}  // namespace kernels
}  // namespace xq
