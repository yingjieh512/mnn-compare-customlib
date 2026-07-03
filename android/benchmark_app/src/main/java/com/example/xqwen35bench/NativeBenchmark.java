package com.example.xqwen35bench;

public final class NativeBenchmark {
    static {
        System.loadLibrary("xqbench_jni");
    }

    private NativeBenchmark() {}

    public static native String runBenchmark(String modelDir, int promptTokens, int maxNewTokens);
}

