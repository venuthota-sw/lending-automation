package com.lending.poc.model;

public record LoanAffordability(
        double requestedLoanAmount,
        double verifiedMonthlyIncome,
        double loanToIncomeRatio,
        String status
) {}
