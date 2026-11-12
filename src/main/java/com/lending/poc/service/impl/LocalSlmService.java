package com.lending.poc.service.impl;

import com.google.gson.Gson;
import com.lending.poc.model.DocumentText;
import com.lending.poc.model.UnderwritingReport;
import com.lending.poc.service.LlmService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

public class LocalSlmService implements LlmService {

    private static final Logger log = LoggerFactory.getLogger(LocalSlmService.class);

    private static String requestId() {
        String id = MDC.get("requestId");
        return id != null ? id : "-";
    }

    private final HttpClient httpClient;
    private final Gson gson;
    private final String endpointUrl;
    private final String modelName;
    private final String systemPrompt;
    private final String userPromptTemplate;
    private final double temperature;
    private final int numPredict;
    private final Duration timeout;

    public LocalSlmService(String endpointUrl, String modelName, String systemPrompt,
                           String userPromptTemplate, double temperature, int numPredict,
                           long timeoutSeconds) {
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(timeoutSeconds))
                .build();
        this.gson = new Gson();
        this.endpointUrl = endpointUrl;
        this.modelName = modelName;
        this.systemPrompt = systemPrompt;
        this.userPromptTemplate = userPromptTemplate;
        this.temperature = temperature;
        this.numPredict = numPredict;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
    }

    @Override
    public UnderwritingReport analyzeDiscrepancies(DocumentText applicationForm, DocumentText verificationDoc) {
        String userPrompt = String.format(
                userPromptTemplate,
                applicationForm.rawText(), verificationDoc.rawText()
        );

        // --- CRITICAL FIX: Inject native "format": "json" constraint payload ---
        Map<String, Object> options = new LinkedHashMap<>();
        options.put("temperature", temperature);
        options.put("num_predict", numPredict);

        Map<String, Object> requestBody = Map.of(
                "model", modelName,
                "prompt", systemPrompt + "\n\n" + userPrompt,
                "format", "json", // Forces Ollama's inner token sampling layers to output standard syntactical JSON
                "stream", false,
                "options", options
        );
        // ----------------------------------------------------------------------

        long startNanos = System.nanoTime();
        log.info("SLM request: model={}, appChars={}, docChars={}",
                modelName,
                applicationForm.rawText() == null ? 0 : applicationForm.rawText().length(),
                verificationDoc.rawText() == null ? 0 : verificationDoc.rawText().length());
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(endpointUrl))
                    .header("Content-Type", "application/json")
                    .header("X-Request-Id", requestId())
                    .timeout(timeout)
                    .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(requestBody)))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                throw new RuntimeException("Ollama returned bad HTTP status code: " + response.statusCode());
            }

            Map<?, ?> responseMap = gson.fromJson(response.body(), Map.class);
            long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
            logOllamaMetrics(responseMap, elapsedMs);
            String rawJsonResponse = null;

            if (responseMap.containsKey("response")) {
                rawJsonResponse = (String) responseMap.get("response");
            } else if (responseMap.containsKey("message")) {
                Map<?, ?> messageMap = (Map<?, ?>) responseMap.get("message");
                if (messageMap != null && messageMap.containsKey("content")) {
                    rawJsonResponse = (String) messageMap.get("content");
                }
            }

            if (rawJsonResponse == null || rawJsonResponse.strip().isEmpty()) {
                throw new RuntimeException("Ollama response text content was empty.");
            }

            // Clean any code block syntax wraps if the model leaks them despite the format check
            rawJsonResponse = rawJsonResponse.replaceAll("```json|```", "").strip();

            // Deserialize string payload straight into your strongly-typed Java DTO Records
            UnderwritingReport report = gson.fromJson(rawJsonResponse, UnderwritingReport.class);
            log.info("SLM response parsed: action={}, discrepancies={}",
                    report.underwritingAction(),
                    report.discrepanciesFound() == null ? 0 : report.discrepanciesFound().size());
            return report;

        } catch (Exception e) {
            long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
            log.error("SLM call failed after {} ms: {}", elapsedMs, e.getMessage(), e);
            throw new RuntimeException("SLM execution or JSON parsing failed", e);
        }
    }

    private void logOllamaMetrics(Map<?, ?> responseMap, long elapsedMs) {
        Object evalCount = responseMap.get("eval_count");
        Object evalDurationNs = responseMap.get("eval_duration");
        Object promptEvalCount = responseMap.get("prompt_eval_count");
        if (evalCount != null) {
            double tokensPerSec = evalDurationNs instanceof Number n && n.longValue() > 0
                    ? ((Number) evalCount).doubleValue() / (n.doubleValue() / 1_000_000_000.0)
                    : 0;
            log.info("Ollama metrics: elapsed={} ms, promptTokens={}, evalTokens={}, ~{:.1f} tok/s",
                    elapsedMs, promptEvalCount, evalCount, tokensPerSec);
        } else {
            log.info("SLM HTTP call completed in {} ms", elapsedMs);
        }
    }
}
