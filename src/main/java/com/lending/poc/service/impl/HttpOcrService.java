package com.lending.poc.service.impl;

import com.google.gson.Gson;
import com.lending.poc.model.DocumentText;
import com.lending.poc.service.OcrService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import java.io.File;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.util.Map;
import java.util.UUID;

public class HttpOcrService implements OcrService {

    private static final Logger log = LoggerFactory.getLogger(HttpOcrService.class);

    private static String requestId() {
        String id = MDC.get("requestId");
        return id != null ? id : "-";
    }

    private final String serverUrl;
    private final HttpClient httpClient;
    private final Gson gson;

    public HttpOcrService(String serverUrl) {
        this.serverUrl = serverUrl;
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .build();
        this.gson = new Gson();
    }

    @Override
    public DocumentText extractText(File documentFile) throws Exception {
        long startNanos = System.nanoTime();
        log.debug("OCR request: file='{}', size={} bytes, server={}",
                documentFile.getName(), documentFile.length(), serverUrl);
        String boundary = "JavaBoundary-" + UUID.randomUUID().toString();
        byte[] fileBytes = Files.readAllBytes(documentFile.toPath());

        // Construct standard multipart/form-data payload body natively
        StringBuilder multipartBody = new StringBuilder();
        multipartBody.append("--").append(boundary).append("\r\n");
        multipartBody.append("Content-Disposition: form-data; name=\"file\"; filename=\"")
                .append(documentFile.getName()).append("\"\r\n");
        multipartBody.append("Content-Type: image/png\r\n\r\n");

        byte[] headerBytes = multipartBody.toString().getBytes("UTF-8");
        byte[] footerBytes = ("\r\n--" + boundary + "--\r\n").getBytes("UTF-8");

        byte[] completePayload = new byte[headerBytes.length + fileBytes.length + footerBytes.length];
        System.arraycopy(headerBytes, 0, completePayload, 0, headerBytes.length);
        System.arraycopy(fileBytes, 0, completePayload, headerBytes.length, fileBytes.length);
        System.arraycopy(footerBytes, 0, completePayload, headerBytes.length + fileBytes.length, footerBytes.length);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(serverUrl + "/extract-text"))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .header("X-Request-Id", requestId())
                .POST(HttpRequest.BodyPublishers.ofByteArray(completePayload))
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;

        if (response.statusCode() != 200) {
            log.error("OCR server error: file='{}', status={}, elapsed={} ms, body={}",
                    documentFile.getName(), response.statusCode(), elapsedMs, response.body());
            throw new RuntimeException("OCR Server returned error status code: " + response.statusCode()
                    + " body: " + response.body());
        }

        Map<?, ?> responseMap = gson.fromJson(response.body(), Map.class);
        if (responseMap.containsKey("error")) {
            log.error("OCR processing error: file='{}', elapsed={} ms, error={}",
                    documentFile.getName(), elapsedMs, responseMap.get("error"));
            throw new RuntimeException("OCR Processing Error: " + responseMap.get("error"));
        }

        String rawText = (String) responseMap.get("text");
        log.info("OCR success: file='{}', elapsed={} ms, extracted={} chars",
                documentFile.getName(), elapsedMs, rawText == null ? 0 : rawText.length());
        return new DocumentText(documentFile.getName(), rawText);
    }
}
