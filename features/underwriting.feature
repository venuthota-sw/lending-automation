Feature: Loan underwriting discrepancy analysis
  As a lending operations analyst
  I want to submit a loan application and verification document through the UI
  So that the system produces an underwriting report highlighting discrepancies

  Background:
    Given I open the lending UI at "http://localhost:4200"

  Scenario: Clean application is approved
    When I upload "loan_application_app-2026-1001.png" as the application form
    And I upload "paystub_emp-1001.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the underwriting action should be "APPROVE"
    And the applicant name status should be "MATCHED"
    And the employer status should be "MATCHED"
    And the address status should be "MATCHED"
    And the ssn status should be "MATCHED"
    And the affordability status should be "MATCHED"

  Scenario: Inflated stated income is flagged
    When I upload "loan_application_app-2026-1002.png" as the application form
    And I upload "paystub_emp-1002.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the underwriting action should be one of "HOLD,REJECT"
    And the income status should be "MISMATCH"

  Scenario: Different applicant name is flagged
    When I upload "loan_application_app-2026-1003.png" as the application form
    And I upload "paystub_emp-90117.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the applicant name status should be "MISMATCH"

  Scenario: Different employer is flagged
    When I upload "loan_application_app-2026-1004.png" as the application form
    And I upload "paystub_emp-55402.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the employer status should be "MISMATCH"

  Scenario: Near-match name with only punctuation differences is accepted
    When I upload "loan_application_app-2026-1005.png" as the application form
    And I upload "paystub_emp-1005.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the applicant name status should be "MATCHED"

  Scenario: Different address on paystub is flagged
    When I upload "loan_application_app-2026-1006.png" as the application form
    And I upload "paystub_emp-1006.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the address status should be "MISMATCH"

  Scenario: Different SSN last-4 on paystub is flagged
    When I upload "loan_application_app-2026-1007.png" as the application form
    And I upload "paystub_emp-1007.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the ssn status should be "MISMATCH"

  Scenario: Loan amount beyond affordable multiple of income is flagged
    When I upload "loan_application_app-2026-1008.png" as the application form
    And I upload "paystub_emp-1008.png" as the verification document
    And I click "Run Underwriting"
    Then the underwriting report should appear
    And the affordability status should be "MISMATCH"
