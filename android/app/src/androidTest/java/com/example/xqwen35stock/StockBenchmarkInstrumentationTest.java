package com.example.xqwen35stock;

import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public final class StockBenchmarkInstrumentationTest {
    @Test
    public void runStockBenchmark() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Bundle args = InstrumentationRegistry.getArguments();
        int promptTokens = parseInt(args.getString("prompt_tokens", ""), 512);
        int maxNewTokens = parseInt(args.getString("max_new_tokens", ""), 256);
        int warmupIterations = parseInt(args.getString("warmup_iterations", ""), 1);
        int measuredIterations = parseInt(args.getString("measured_iterations", ""), 5);
        int validationMaxNewTokens = parseInt(args.getString("validation_max_new_tokens", ""), 32);
        boolean runQualityValidation = parseBoolean(args.getString("run_quality_validation", "false"));
        String backend = sanitizeBackend(args.getString("backend", "cpu"));
        boolean allowBackendFailure = parseBoolean(args.getString("allow_backend_failure", "false"));
        File root = context.getExternalFilesDir(null);
        File dir = ModelBootstrap.resolveModelDir(context);
        if (runQualityValidation) {
            String json = NativeStockBenchmark.runQualityValidation(
                    dir.getAbsolutePath(),
                    backend,
                    validationMaxNewTokens);
            Log.i("XQBENCH", "BENCH_QUALITY_JSON " + json);
            if (root != null) {
                File artifactDir = new File(root, "bench_artifacts");
                if (!artifactDir.mkdirs() && !artifactDir.isDirectory()) {
                    throw new IllegalStateException("failed to create " + artifactDir.getAbsolutePath());
                }
                try (FileOutputStream out = new FileOutputStream(
                        new File(artifactDir, "quality_validation_stock.json"))) {
                    out.write(json.getBytes(StandardCharsets.UTF_8));
                }
            }
            if (!json.contains("\"status\":\"ok\"") && !(allowBackendFailure && !backend.equals("cpu"))) {
                throw new AssertionError("Quality validation returned non-ok JSON: " + json);
            }
            if (!json.contains("\"quality_gate_passed\":true") && !(allowBackendFailure && !backend.equals("cpu"))) {
                throw new AssertionError("stock quality sanity gate failed: " + json);
            }
            return;
        }
        String json = NativeStockBenchmark.runBenchmark(
                dir.getAbsolutePath(),
                backend,
                promptTokens,
                maxNewTokens,
                warmupIterations,
                measuredIterations);
        Log.i("XQBENCH", "BENCH_RESULT_JSON " + json);
        if (root != null) {
            File artifactDir = new File(root, "bench_artifacts");
            if (!artifactDir.mkdirs() && !artifactDir.isDirectory()) {
                throw new IllegalStateException("failed to create " + artifactDir.getAbsolutePath());
            }
            try (FileOutputStream out = new FileOutputStream(
                    new File(artifactDir, "stock_mnn_" + backend + "_benchmark.json"))) {
                out.write(json.getBytes(StandardCharsets.UTF_8));
            }
        }
        if (!json.contains("\"status\":\"ok\"") && !(allowBackendFailure && !backend.equals("cpu"))) {
            throw new AssertionError("Benchmark returned non-ok JSON: " + json);
        }
        if (!json.contains("\"backend_requested\":\"" + backend + "\"")) {
            throw new AssertionError("stock backend request evidence missing: " + json);
        }
    }

    private static int parseInt(String value, int fallback) {
        try {
            return value == null || value.isEmpty() ? fallback : Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    private static boolean parseBoolean(String value) {
        return value != null && value.equalsIgnoreCase("true");
    }

    private static String sanitizeBackend(String value) {
        if (value == null || value.isEmpty()) {
            return "cpu";
        }
        String normalized = value.toLowerCase();
        if (normalized.equals("cpu")
                || normalized.equals("vulkan")
                || normalized.equals("opencl")
                || normalized.equals("nnapi")) {
            return normalized;
        }
        return "cpu";
    }
}
