package com.lending.poc.service.impl;

import com.lending.poc.model.DocumentText;
import com.lending.poc.service.OcrService;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;

public class PaddleOcrService implements OcrService {

    private final String pythonExecutable;
    private final String pythonScriptPath;

    public PaddleOcrService(String pythonExecutable, String pythonScriptPath) {
        this.pythonExecutable = pythonExecutable;
        this.pythonScriptPath = pythonScriptPath;
    }

    @Override
    public DocumentText extractText(File documentFile) throws Exception {
        ProcessBuilder processBuilder = new ProcessBuilder(
                this.pythonExecutable,
                this.pythonScriptPath,
                documentFile.getAbsolutePath()
        );

        // --- THE CRITICAL FIX: Environment Injection ---
        // This forces Java to inject the exact system paths Python needs to map its C++ DLLs
        java.util.Map<String, String> env = processBuilder.environment();

        // Explicitly place your venv binary directory at the absolute front of the PATH variable
        File venvScriptsDir = new File(this.pythonExecutable).getParentFile();
        String systemPath = System.getenv("PATH");
        env.put("PATH", venvScriptsDir.getAbsolutePath() + File.pathSeparator + systemPath);

        // Quiet down C++ optimizations that cause Windows background process crashes
        env.put("GLOG_minloglevel", "3");
        env.put("OMP_NUM_THREADS", "1");
        // ------------------------------------------------

        processBuilder.redirectErrorStream(true);
        Process process = processBuilder.start();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {

            String rawText = reader.lines().collect(Collectors.joining("\n"));
            int exitCode = process.waitFor();

            if (exitCode != 0) {
                throw new RuntimeException("PaddleOCR process failed with exit code " + exitCode + ". Output:\n" + rawText);
            }

            return new DocumentText(documentFile.getName(), rawText);
        }
    }
}
