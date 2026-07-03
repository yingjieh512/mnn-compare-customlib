package com.example.xqwen35bench;

import android.content.Context;
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
        File dir = context.getExternalFilesDir(null);
        String json = NativeBenchmark.runBenchmark(dir == null ? "" : dir.getAbsolutePath(), 512, 256);
        Log.i("XQBENCH", "BENCH_RESULT_JSON " + json);
        if (dir != null) {
            try (FileOutputStream out = new FileOutputStream(new File(dir, "customlib_benchmark.json"))) {
                out.write(json.getBytes(StandardCharsets.UTF_8));
            }
        }
    }
}

