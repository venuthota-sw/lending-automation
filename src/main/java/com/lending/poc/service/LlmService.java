package com.lending.poc.service;

import com.lending.poc.model.DocumentText;
import com.lending.poc.model.UnderwritingReport;

public interface LlmService {
    UnderwritingReport analyzeDiscrepancies(DocumentText applicationForm, DocumentText verificationDoc);
}
