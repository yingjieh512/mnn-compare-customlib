package com.example.xqwen35stock;

public final class NativeStockBenchmark {
    static {
        System.loadLibrary("xqstock_jni");
    }

    private NativeStockBenchmark() {}

    public static native String runBenchmark(
            String modelDir,
            String backend,
            int promptTokens,
            int maxNewTokens,
            int warmupIterations,
            int measuredIterations);

    public static native String runQualityValidation(
            String modelDir,
            String backend,
            int maxNewTokens);
}
