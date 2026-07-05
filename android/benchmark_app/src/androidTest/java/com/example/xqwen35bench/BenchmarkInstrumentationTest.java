package com.example.xqwen35bench;

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
public final class BenchmarkInstrumentationTest {
    @Test
    public void runCustomBenchmark() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Bundle args = InstrumentationRegistry.getArguments();
        int promptTokens = parseInt(args.getString("prompt_tokens", ""), 512);
        int maxNewTokens = parseInt(args.getString("max_new_tokens", ""), 256);
        int warmupIterations = parseInt(args.getString("warmup_iterations", ""), 1);
        int measuredIterations = parseInt(args.getString("measured_iterations", ""), 5);
        String customBackend = sanitizeBackend(args.getString("custom_backend", args.getString("backend", "cpu")));
        File root = context.getExternalFilesDir(null);
        File dir = ModelBootstrap.resolveModelDir(context);
        String json = NativeBenchmark.runBenchmark(
                dir.getAbsolutePath(),
                customBackend,
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
                    new File(artifactDir, "customlib_" + customBackend + "_benchmark.json"))) {
                out.write(json.getBytes(StandardCharsets.UTF_8));
            }
        }
        if (!json.contains("\"status\":\"ok\"")) {
            throw new AssertionError("Benchmark returned non-ok JSON: " + json);
        }
        if (!json.contains("\"hotpath_replaced\":true")) {
            throw new AssertionError("custom hotpath replacement evidence missing: " + json);
        }
        if (!json.contains("\"full_custom_decode\":true")) {
            throw new AssertionError("full custom decode evidence missing: " + json);
        }
        if (!json.contains("\"fallback_op_families\":[]")) {
            throw new AssertionError("custom fallback list is not empty: " + json);
        }
        if (!json.contains("\"calls_mnn_llm_response_for_measured_generation\":false")) {
            throw new AssertionError("custom path MNN-response evidence missing: " + json);
        }
        if (!json.contains("\"custom_backend_requested\":\"" + customBackend + "\"")) {
            throw new AssertionError("custom backend request evidence missing: " + json);
        }
        if (!json.contains("\"custom_backend_actual\"")) {
            throw new AssertionError("custom backend actual evidence missing: " + json);
        }
        if (!json.contains("\"lm_head_custom\"") || !json.contains("\"sampling_greedy_custom\"")) {
            throw new AssertionError("custom lm_head/sampling trace evidence missing: " + json);
        }
    }

    private static int parseInt(String value, int fallback) {
        try {
            return value == null || value.isEmpty() ? fallback : Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    private static String sanitizeBackend(String value) {
        if (value == null || value.isEmpty()) {
            return "cpu";
        }
        String normalized = value.toLowerCase();
        if (normalized.equals("cpu") || normalized.equals("vulkan") || normalized.equals("cpu_vulkan_hybrid")) {
            return normalized;
        }
        return "cpu";
    }
}
