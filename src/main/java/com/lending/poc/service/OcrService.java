package com.lending.poc.service;

import com.lending.poc.model.DocumentText;
import java.io.File;

public interface OcrService {
    DocumentText extractText(File documentFile) throws Exception;
}
