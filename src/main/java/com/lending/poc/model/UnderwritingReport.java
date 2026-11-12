package com.lending.poc.model;

import java.util.List;

public record UnderwritingReport(
        String applicationId,
        FieldValidation applicantName,
        IncomeValidation incomeValidation,
        FieldValidation employerValidation,
        FieldValidation addressValidation,
        FieldValidation ssnValidation,
        LoanAffordability loanAffordability,
        List<Discrepancy> discrepanciesFound,
        String underwritingAction
) {}
