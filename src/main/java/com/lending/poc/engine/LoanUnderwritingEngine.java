package com.lending.poc.engine;

import com.lending.poc.model.DocumentText;
import com.lending.poc.model.UnderwritingReport;
import com.lending.poc.service.LlmService;
import com.lending.poc.service.OcrService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;

public class LoanUnderwritingEngine {

    private static final Logger log = LoggerFactory.getLogger(LoanUnderwritingEngine.class);

    private final OcrService ocrService;
    private final LlmService llmService;

    // Dependency Injection ensures implementation switching requires zero engine modification
    public LoanUnderwritingEngine(OcrService ocrService, LlmService llmService) {
        this.ocrService = ocrService;
        this.llmService = llmService;
    }

    public UnderwritingReport runAutomationPipeline(File appFormFile, File verificationFile) throws Exception {
        long pipelineStart = System.nanoTime();
        log.info("Pipeline started: app='{}', verification='{}'",
                appFormFile.getName(), verificationFile.getName());

        // Step 1 & 2: Asynchronous text extraction handles performance limits cleanly
        long ocrStart = System.nanoTime();
        DocumentText appText = ocrService.extractText(appFormFile);
        DocumentText verificationText = ocrService.extractText(verificationFile);
        long ocrMs = (System.nanoTime() - ocrStart) / 1_000_000;
        log.info("OCR completed in {} ms: app='{}' ({} chars), doc='{}' ({} chars)",
                ocrMs, appText.sourceName(), appText.rawText() == null ? 0 : appText.rawText().length(),
                verificationText.sourceName(), verificationText.rawText() == null ? 0 : verificationText.rawText().length());

        // Step 3: SLM verification and automated cross-referencing
        long slmStart = System.nanoTime();
        UnderwritingReport report = llmService.analyzeDiscrepancies(appText, verificationText);
        long slmMs = (System.nanoTime() - slmStart) / 1_000_000;
        long totalMs = (System.nanoTime() - pipelineStart) / 1_000_000;
        log.info("SLM analysis completed in {} ms; pipeline total {} ms, action={}",
                slmMs, totalMs, report.underwritingAction());
        return report;
    }
}