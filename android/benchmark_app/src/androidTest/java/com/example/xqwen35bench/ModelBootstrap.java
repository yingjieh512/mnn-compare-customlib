package com.example.xqwen35bench;

import android.content.Context;
import android.os.Bundle;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

final class ModelBootstrap {
    private ModelBootstrap() {}

    static File resolveModelDir(Context context) throws Exception {
        File root = context.getExternalFilesDir(null);
        if (root == null) {
            throw new IllegalStateException("external files dir is null");
        }
        if (!root.mkdirs() && !root.isDirectory()) {
            throw new IllegalStateException("failed to create " + root.getAbsolutePath());
        }

        StringBuilder discovery = new StringBuilder();
        Bundle args = InstrumentationRegistry.getArguments();
        String explicitDir = args.getString("model_dir", "");
        if (!explicitDir.isEmpty()) {
            File dir = new File(explicitDir);
            discovery.append("explicit model_dir=").append(dir.getAbsolutePath()).append('\n');
            if (isUsableModelDir(dir)) {
                writeBootstrap(root, dir, discovery, "explicit");
                return dir;
            }
        }

        File existing = findModelDir(root, discovery);
        if (existing != null) {
            writeBootstrap(root, existing, discovery, "existing");
            return existing;
        }

        List<String> partUrls = urlsFromArgs(args, "model_zip_part_urls", "model_zip_part_urls_file");
        if (!partUrls.isEmpty()) {
            File zip = new File(root, "qwen35_model.zip");
            discovery.append("model zip part urls provided count=").append(partUrls.size()).append('\n');
            downloadParts(partUrls, zip, discovery);
            String expected = args.getString("model_zip_sha256", "");
            if (!expected.isEmpty()) {
                String actual = sha256(zip);
                discovery.append("model_zip_sha256=").append(actual).append('\n');
                if (!expected.equalsIgnoreCase(actual)) {
                    throw new IllegalStateException("model zip sha256 mismatch expected=" + expected + " actual=" + actual);
                }
            }
            unzip(zip, root);
            cleanupZip(zip, discovery);
        } else {
            String url = urlFromArgs(args, "model_zip_url", "model_zip_url_file");
            if (url != null && !url.isEmpty()) {
                File zip = new File(root, "qwen35_model.zip");
                discovery.append("download url provided\n");
                download(url, zip);
                String expected = args.getString("model_zip_sha256", "");
                if (!expected.isEmpty()) {
                    String actual = sha256(zip);
                    discovery.append("model_zip_sha256=").append(actual).append('\n');
                    if (!expected.equalsIgnoreCase(actual)) {
                        throw new IllegalStateException("model zip sha256 mismatch expected=" + expected + " actual=" + actual);
                    }
                }
                unzip(zip, root);
                cleanupZip(zip, discovery);
            }
        }

        String embeddingUrl = urlFromArgs(args, "embedding_zip_url", "embedding_zip_url_file");
        if (embeddingUrl != null && !embeddingUrl.isEmpty()) {
            File zip = new File(root, "qwen35_embeddings.zip");
            discovery.append("embedding url provided\n");
            download(embeddingUrl, zip);
            String expected = args.getString("embedding_zip_sha256", "");
            if (!expected.isEmpty()) {
                String actual = sha256(zip);
                discovery.append("embedding_zip_sha256=").append(actual).append('\n');
                if (!expected.equalsIgnoreCase(actual)) {
                    throw new IllegalStateException("embedding zip sha256 mismatch expected=" + expected + " actual=" + actual);
                }
            }
            unzip(zip, root);
            cleanupZip(zip, discovery);
        }

        File dir = findModelDir(root, discovery);
        if (dir == null) {
            writeDiscovery(root, discovery);
            throw new IllegalStateException("unable to locate Qwen3.5 model dir under " + root.getAbsolutePath());
        }
        writeBootstrap(root, dir, discovery, "downloaded");
        return dir;
    }

    private static String urlFromArgs(Bundle args, String directKey, String fileKey) throws IOException {
        String direct = args.getString(directKey, "");
        if (!direct.isEmpty()) {
            return direct;
        }
        String file = args.getString(fileKey, "");
        if (file.isEmpty()) {
            return "";
        }
        return readText(new File(file)).trim();
    }

    private static List<String> urlsFromArgs(Bundle args, String directKey, String fileKey) throws IOException {
        String text = args.getString(directKey, "");
        if (text.isEmpty()) {
            String file = args.getString(fileKey, "");
            if (!file.isEmpty()) {
                text = readText(new File(file));
            }
        }
        List<String> urls = new ArrayList<>();
        for (String line : text.split("\\r?\\n")) {
            String trimmed = line.trim();
            if (!trimmed.isEmpty()) {
                urls.add(trimmed);
            }
        }
        return urls;
    }

    private static boolean isUsableModelDir(File dir) {
        return new File(dir, "llm_config.json").isFile()
                && new File(dir, "llm.mnn").isFile()
                && new File(dir, "llm.mnn.weight").isFile()
                && new File(dir, "tokenizer.mtok").isFile()
                && new File(dir, "embeddings_bf16.bin").isFile()
                && new File(dir, "xqwen35_manifest.json").isFile()
                && new File(dir, "lm_head_weight.xq4").isFile()
                && new File(dir, "layers_3_self_attn_q_proj_weight.xq4").isFile()
                && new File(dir, "layers_0_linear_attn_in_proj_qkv_weight.xq4").isFile()
                && new File(dir, "layers_0_linear_attn_in_proj_a_weight.xq4").isFile()
                && new File(dir, "layers_0_linear_attn_in_proj_b_weight.xq4").isFile()
                && new File(dir, "layers_0_linear_attn_conv1d_weight.f32").isFile()
                && new File(dir, "layers_0_linear_attn_A_log.f32").isFile()
                && new File(dir, "layers_0_linear_attn_dt_bias.f32").isFile();
    }

    private static File findModelDir(File root, StringBuilder discovery) {
        List<File> queue = new ArrayList<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            File dir = queue.remove(0);
            discovery.append("scan ").append(dir.getAbsolutePath()).append('\n');
            if (isUsableModelDir(dir)) {
                return dir;
            }
            File[] children = dir.listFiles();
            if (children == null) {
                continue;
            }
            for (File child : children) {
                if (child.isDirectory()) {
                    queue.add(child);
                }
            }
        }
        return null;
    }

    private static void download(String url, File dst) throws IOException {
        downloadAppend(url, dst, false);
    }

    private static void downloadParts(List<String> urls, File dst, StringBuilder discovery) throws IOException {
        if (dst.exists() && !dst.delete()) {
            throw new IOException("failed to delete partial " + dst);
        }
        long total = 0;
        for (int i = 0; i < urls.size(); ++i) {
            long bytes = downloadAppend(urls.get(i), dst, i > 0);
            total += bytes;
            discovery.append("model_zip_part_").append(i)
                    .append("_bytes=").append(bytes)
                    .append(" total=").append(total)
                    .append('\n');
        }
    }

    private static long downloadAppend(String url, File dst, boolean append) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setConnectTimeout(30000);
        conn.setReadTimeout(120000);
        conn.connect();
        int code = conn.getResponseCode();
        if (code < 200 || code >= 300) {
            throw new IOException("download failed code=" + code);
        }
        long bytes = 0;
        try (InputStream in = new BufferedInputStream(conn.getInputStream());
             FileOutputStream fos = new FileOutputStream(dst, append);
             BufferedOutputStream out = new BufferedOutputStream(fos)) {
            byte[] buf = new byte[1024 * 1024];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
                bytes += n;
            }
        } finally {
            conn.disconnect();
        }
        return bytes;
    }

    private static void cleanupZip(File zip, StringBuilder discovery) {
        if (zip.exists()) {
            discovery.append("delete_zip_after_unzip=").append(zip.delete()).append('\n');
        }
    }

    private static void unzip(File zip, File root) throws IOException {
        String canonicalRoot = root.getCanonicalPath() + File.separator;
        try (ZipInputStream in = new ZipInputStream(new BufferedInputStream(new FileInputStream(zip)))) {
            ZipEntry entry;
            byte[] buf = new byte[1024 * 1024];
            while ((entry = in.getNextEntry()) != null) {
                File outFile = new File(root, entry.getName());
                String canonical = outFile.getCanonicalPath();
                if (!canonical.startsWith(canonicalRoot)) {
                    throw new IOException("zip entry escapes root: " + entry.getName());
                }
                if (entry.isDirectory()) {
                    if (!outFile.mkdirs() && !outFile.isDirectory()) {
                        throw new IOException("failed to create " + outFile);
                    }
                } else {
                    File parent = outFile.getParentFile();
                    if (parent != null && !parent.mkdirs() && !parent.isDirectory()) {
                        throw new IOException("failed to create " + parent);
                    }
                    try (FileOutputStream fos = new FileOutputStream(outFile);
                         BufferedOutputStream out = new BufferedOutputStream(fos)) {
                        int n;
                        while ((n = in.read(buf)) >= 0) {
                            out.write(buf, 0, n);
                        }
                    }
                }
                in.closeEntry();
            }
        }
    }

    private static String readText(File file) throws IOException {
        try (FileInputStream in = new FileInputStream(file);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) >= 0) {
                out.write(buf, 0, n);
            }
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    private static String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buf = new byte[1024 * 1024];
            int n;
            while ((n = in.read(buf)) >= 0) {
                digest.update(buf, 0, n);
            }
        }
        StringBuilder sb = new StringBuilder();
        for (byte b : digest.digest()) {
            sb.append(String.format(Locale.US, "%02x", b & 0xff));
        }
        return sb.toString();
    }

    private static void writeBootstrap(File root, File modelDir, StringBuilder discovery, String source) throws IOException {
        writeDiscovery(root, discovery);
        String json = "{\"source\":\"" + source + "\",\"model_dir\":\"" + escape(modelDir.getAbsolutePath()) + "\"}";
        try (FileOutputStream out = new FileOutputStream(new File(root, "model_bootstrap.json"))) {
            out.write(json.getBytes(StandardCharsets.UTF_8));
        }
    }

    private static void writeDiscovery(File root, StringBuilder discovery) throws IOException {
        try (FileOutputStream out = new FileOutputStream(new File(root, "model_bootstrap_discovery.txt"))) {
            out.write(discovery.toString().getBytes(StandardCharsets.UTF_8));
        }
    }

    private static String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
