import { Component, OnInit } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../../../dialog/simple-dialog.component';
import { FormSettings } from '../../../interfaces/forms.interfaces';
import { Loadable } from '../../../interfaces/loadable';
import { CreateFormAction, DeleteFormAction, GetFormsAction } from '../../forms.actions';
import { FormsState, getForms } from '../../forms.state';

@Component({
  selector: 'oca-form-list-page',
  template: `
    <ng-container *ngIf="forms$ | async as forms">
      <oca-forms-list [forms]="forms" (createForm)="createForm()" (deleteForm)="deleteForm($event)"></oca-forms-list>
      <div class="fab-bottom-right">
        <a mat-fab (click)="createForm()">
          <mat-icon>add</mat-icon>
        </a>
      </div>
    </ng-container>`,
})
export class FormListPageComponent implements OnInit {
  creating = false;
  forms$: Observable<Loadable<FormSettings[]>>;

  constructor(private _store: Store<FormsState>,
              private _matDialog: MatDialog,
              private _translate: TranslateService) {
  }

  ngOnInit() {
    this._store.dispatch(new GetFormsAction());
    this.forms$ = this._store.pipe(select(getForms));
  }

  createForm() {
    if (!this.creating) {
      this._store.dispatch(new CreateFormAction());
      this.creating = true;
    }
  }

  deleteForm(form: FormSettings) {
    const config: MatDialogConfig<SimpleDialogData> = {
      data: {
        title: this._translate.instant('oca.confirm'),
        message: this._translate.instant('oca.confirm_delete_form'),
        ok: this._translate.instant('oca.yes'),
        cancel: this._translate.instant('oca.cancel'),
      },
    };
    this._matDialog.open(SimpleDialogComponent, config).afterClosed().subscribe((result: SimpleDialogResult) => {
      if (result && result.submitted) {
        this._store.dispatch(new DeleteFormAction(form));
      }
    });
  }
}
