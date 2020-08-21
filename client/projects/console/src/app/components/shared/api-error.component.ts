import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { ApiErrorService } from '../../services';

@Component({
  selector: 'rcc-api-request-status',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div fxLayoutAlign="center center">
      <mat-progress-spinner mode="indeterminate" *ngIf="status.loading" [diameter]="64"
                            [strokeWidth]="6"></mat-progress-spinner>
    </div>
    <div *ngIf="status.error && !status.success">
      <p class="error-message" [innerText]="getErrorMessage()"></p>
    </div>`,
  styles: [`:host{
    display: block;
    margin: 0 16px;
  }`]
})
export class ApiRequestStatusComponent {
  @Input() status: ApiRequestStatus;

  constructor(private errService: ApiErrorService) {
  }

  getErrorMessage(): string {
    return this.errService.getErrorMessage(this.status.error);
  }
}
