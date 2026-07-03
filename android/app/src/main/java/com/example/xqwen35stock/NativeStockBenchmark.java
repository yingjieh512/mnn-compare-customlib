package com.example.xqwen35stock;

public final class NativeStockBenchmark {
    static {
        System.loadLibrary("xqstock_jni");
    }

    private NativeStockBenchmark() {}

    public static native String runBenchmark(String modelDir, int promptTokens, int maxNewTokens);
}

