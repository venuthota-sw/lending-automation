package com.lending.poc;

import com.lending.poc.engine.LoanUnderwritingEngine;
import com.lending.poc.service.LlmService;
import com.lending.poc.service.OcrService;
import com.lending.poc.service.impl.HttpOcrService;
import com.lending.poc.service.impl.LocalSlmService;
import com.lending.poc.service.impl.PaddleOcrService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class MainApplication {

    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }

    @Bean
    @ConditionalOnProperty(name = "ocr.provider", havingValue = "http", matchIfMissing = true)
    public OcrService httpOcrService(@Value("${ocr.server-url}") String serverUrl) {
        return new HttpOcrService(serverUrl);
    }

    @Bean
    @ConditionalOnProperty(name = "ocr.provider", havingValue = "paddle")
    public OcrService paddleOcrService(
            @Value("${ocr.paddle.python-executable}") String pythonExecutable,
            @Value("${ocr.paddle.script-path}") String pythonScriptPath) {
        return new PaddleOcrService(pythonExecutable, pythonScriptPath);
    }

    @Bean
    public LlmService llmService(
            @Value("${slm.endpoint-url}") String endpointUrl,
            @Value("${slm.model-name}") String modelName,
            @Value("${slm.prompts.system}") String systemPrompt,
            @Value("${slm.prompts.user-template}") String userPromptTemplate,
            @Value("${slm.options.temperature:0.0}") double temperature,
            @Value("${slm.options.num-predict:1024}") int numPredict,
            @Value("${slm.timeout-seconds:120}") long timeoutSeconds) {
        return new LocalSlmService(endpointUrl, modelName, systemPrompt, userPromptTemplate,
                temperature, numPredict, timeoutSeconds);
    }

    @Bean
    public LoanUnderwritingEngine loanUnderwritingEngine(OcrService ocrService, LlmService llmService) {
        return new LoanUnderwritingEngine(ocrService, llmService);
    }
}
