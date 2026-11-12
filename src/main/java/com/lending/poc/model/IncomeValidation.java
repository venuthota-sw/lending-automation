package com.lending.poc.model;

public record IncomeValidation(
        double statedIncome,
        double verifiedIncome,
        String status,
        double variancePercentage
) {}
