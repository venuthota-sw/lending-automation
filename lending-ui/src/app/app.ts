import { Component, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface FieldValidation {
  formValue: string;
  docValue: string;
  status: string;
}

interface IncomeValidation {
  statedIncome: number;
  verifiedIncome: number;
  status: string;
  variancePercentage: number;
}

interface LoanAffordability {
  requestedLoanAmount: number;
  verifiedMonthlyIncome: number;
  loanToIncomeRatio: number;
  status: string;
}

interface Discrepancy {
  field: string;
  severity: string;
  description: string;
}

interface UnderwritingReport {
  applicationId: string;
  applicantName: FieldValidation;
  incomeValidation: IncomeValidation;
  employerValidation: FieldValidation;
  addressValidation: FieldValidation;
  ssnValidation: FieldValidation;
  loanAffordability: LoanAffordability;
  discrepanciesFound: Discrepancy[];
  underwritingAction: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly apiUrl = 'http://localhost:8081/api/underwrite';

  applicationForm: File | null = null;
  verificationDoc: File | null = null;
  loading = signal(false);
  report = signal<UnderwritingReport | null>(null);
  error = signal<string | null>(null);
  elapsedMs = signal<number | null>(null);
  private elapsedTimer: ReturnType<typeof setInterval> | null = null;

  constructor(private http: HttpClient) {}

  onFileSelected(event: Event, target: 'app' | 'ver') {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (target === 'app') this.applicationForm = file;
    else this.verificationDoc = file;
  }

  submit() {
    if (!this.applicationForm || !this.verificationDoc) {
      this.error.set('Please select both documents before submitting.');
      return;
    }

    const formData = new FormData();
    formData.append('applicationForm', this.applicationForm);
    formData.append('verificationDoc', this.verificationDoc);

    this.loading.set(true);
    this.error.set(null);
    this.report.set(null);

    const startedAt = performance.now();
    const requestId = crypto.randomUUID();
    this.elapsedMs.set(0);
    this.elapsedTimer = setInterval(() => {
      this.elapsedMs.set(Math.round(performance.now() - startedAt));
    }, 250);
    console.log('[ui] Underwrite request sent', {
      requestId,
      app: this.applicationForm.name,
      doc: this.verificationDoc.name,
    });

    this.http.post<UnderwritingReport>(this.apiUrl, formData, {
      headers: { 'X-Request-Id': requestId },
    }).subscribe({
      next: (report) => {
        const elapsedMs = Math.round(performance.now() - startedAt);
        console.log('[ui] Underwrite response received', {
          requestId,
          elapsedMs,
          action: report.underwritingAction,
          discrepancies: report.discrepanciesFound?.length ?? 0,
        });
        this.report.set(report);
        this.loading.set(false);
        this.stopElapsedTimer();
        this.elapsedMs.set(elapsedMs);
      },
      error: (err) => {
        const elapsedMs = Math.round(performance.now() - startedAt);
        console.error('[ui] Underwrite request failed', {
          requestId,
          elapsedMs,
          status: err.status,
          message: err.error?.error ?? err.message,
        });
        this.error.set(err.error?.error ?? 'Request failed. Is the backend running on port 8081?');
        this.loading.set(false);
        this.stopElapsedTimer();
        this.elapsedMs.set(elapsedMs);
      },
    });
  }

  private stopElapsedTimer() {
    if (this.elapsedTimer !== null) {
      clearInterval(this.elapsedTimer);
      this.elapsedTimer = null;
    }
  }

  formatElapsed(ms: number | null): string {
    if (ms === null) return '0.0 s';
    return `${(ms / 1000).toFixed(1)} s`;
  }

  statusClass(status: string | undefined): string {
    return status === 'MATCHED' ? 'status-matched' : 'status-mismatch';
  }

  actionClass(action: string | undefined): string {
    switch (action) {
      case 'APPROVE': return 'action-approve';
      case 'REJECT': return 'action-reject';
      default: return 'action-hold';
    }
  }
}
