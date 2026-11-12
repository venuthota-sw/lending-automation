package com.lending.poc.controller;

import com.lending.poc.engine.LoanUnderwritingEngine;
import com.lending.poc.model.UnderwritingReport;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "${app.cors.allowed-origins:http://localhost:4200}")
public class UnderwritingController {

    private static final Logger log = LoggerFactory.getLogger(UnderwritingController.class);

    private final LoanUnderwritingEngine engine;

    public UnderwritingController(LoanUnderwritingEngine engine) {
        this.engine = engine;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

    @PostMapping("/underwrite")
    public ResponseEntity<?> underwrite(
            @RequestParam("applicationForm") MultipartFile applicationForm,
            @RequestParam("verificationDoc") MultipartFile verificationDoc) {

        if (applicationForm.isEmpty() || verificationDoc.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Both applicationForm and verificationDoc files are required"));
        }

        Path appTemp = null;
        Path verTemp = null;
        long startNanos = System.nanoTime();
        log.info("Underwrite request received: app='{}' ({} bytes), doc='{}' ({} bytes)",
                applicationForm.getOriginalFilename(), applicationForm.getSize(),
                verificationDoc.getOriginalFilename(), verificationDoc.getSize());
        try {
            appTemp = saveTemp(applicationForm);
            verTemp = saveTemp(verificationDoc);

            UnderwritingReport report = engine.runAutomationPipeline(appTemp.toFile(), verTemp.toFile());
            long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
            log.info("Underwrite completed in {} ms: action={}, discrepancies={}",
                    elapsedMs, report.underwritingAction(),
                    report.discrepanciesFound() == null ? 0 : report.discrepanciesFound().size());
            return ResponseEntity.ok(report);

        } catch (Exception e) {
            long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
            log.error("Underwrite failed after {} ms: {}", elapsedMs, e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Underwriting pipeline failed: " + e.getMessage()));
        } finally {
            deleteQuietly(appTemp);
            deleteQuietly(verTemp);
        }
    }

    private Path saveTemp(MultipartFile file) throws IOException {
        String suffix = file.getOriginalFilename() != null && file.getOriginalFilename().contains(".")
                ? file.getOriginalFilename().substring(file.getOriginalFilename().lastIndexOf('.'))
                : ".png";
        Path temp = Files.createTempFile("kyc_", suffix);
        file.transferTo(temp);
        return temp;
    }

    private void deleteQuietly(Path path) {
        if (path != null) {
            try {
                Files.deleteIfExists(path);
            } catch (IOException ignored) {
            }
        }
    }
}
