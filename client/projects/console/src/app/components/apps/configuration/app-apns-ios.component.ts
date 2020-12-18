import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { SaveAppAPNsIosAction } from '../../../actions';
import { saveAppAPNsIosStatus } from '../../../console.state';
import { FileSelector } from '../../../util';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  template: `
    <mat-toolbar>
      <button mat-icon-button [routerLink]="['..']">
        <mat-icon>arrow_back</mat-icon>
      </button>
      <h2>{{ 'rcc.save_apns_settings' | translate }}</h2>
    </mat-toolbar>
    <rcc-api-request-status [status]="createStatus$ | async" class="form-row"></rcc-api-request-status>
    <div class="default-component-margin-full">
      <form #form="ngForm" (ngSubmit)="save()" class="default-component-margin">
      	<mat-form-field>
      		<input matInput name="keyId" [placeholder]="'rcc.key_id' | translate" [(ngModel)]="keyId" required>
      	</mat-form-field>
        <div class="form-row">
          <input type="file" name="file" [accept]="'application/pkcs8'" required
                (change)="onFilePicked($event)" #file>
        </div>
        <div class="form-row">
          <button mat-button mat-raised-button color="primary"
                  [disabled]="!form.form.valid || !file.value || !keyId">
            {{ 'rcc.save' | translate }}
          </button>
        </div>
      </form>
    </div>`,
})
export class AppAPNsIosComponent extends FileSelector implements OnInit {
  createStatus$: Observable<ApiRequestStatus>;
  keyId: string;
  file: string | null;

  constructor(private store: Store,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  ngOnInit() {
    this.createStatus$ = this.store.pipe(select(saveAppAPNsIosStatus));
  }

  save() {
    if (!this.file) {
      return;
    }

    this.store.dispatch(new SaveAppAPNsIosAction(this.keyId, this.file));
  }

  onFileSelected(file: File) {
    this.file = null;
    this.readFile(file);
  }

  onReadCompleted(data: string) {
    this.file = data;
    this.cdRef.markForCheck();
  }
}
