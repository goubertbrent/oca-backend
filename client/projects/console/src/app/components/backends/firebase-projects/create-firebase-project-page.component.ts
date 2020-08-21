import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { CreateFirebaseProjectAction } from '../../../actions';
import { createFirebaseProjectStatus } from '../../../console.state';
import { ConsoleState } from '../../../reducers';
import { FileSelector } from '../../../util';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-toolbar>
      <button mat-icon-button [routerLink]="['..']">
        <mat-icon>arrow_back</mat-icon>
      </button>
      <h2>{{ 'rcc.create_firebase_project' | translate }}</h2>
    </mat-toolbar>
    <rcc-api-request-status [status]="createStatus$ | async" class="form-row"></rcc-api-request-status>
    <div class="default-component-margin-full">
      <form #form="ngForm" (ngSubmit)="save()" class="default-component-margin">
        <div class="form-row">
          <input type="file" name="file" [accept]="'application/json'" required
                (change)="onFilePicked($event)" #file>
        </div>
        <div class="form-row">
          <button mat-button mat-raised-button color="primary"
                  [disabled]="!form.form.valid || !file.value">
            {{ 'rcc.save' | translate }}
          </button>
        </div>
      </form>
    </div>`,
})
export class CreateFirebaseProjectPageComponent extends FileSelector implements OnInit {
  createStatus$: Observable<ApiRequestStatus>;
  file: string | null;


  constructor(private store: Store,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  ngOnInit() {
    this.createStatus$ = this.store.pipe(select(createFirebaseProjectStatus));
  }

  save() {
    if (!this.file) {
      return;
    }

    this.store.dispatch(new CreateFirebaseProjectAction(this.file));
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
