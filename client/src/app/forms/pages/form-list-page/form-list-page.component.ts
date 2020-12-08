import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { Loadable, NonNullLoadable } from '../../../shared/loadable/loadable';
import { CreateFormAction, DeleteFormAction, GetFormsAction } from '../../forms.actions';
import { FormsState, getForms, getIntegrations } from '../../forms.state';
import { FormIntegrationConfiguration } from '../../integrations/integrations';
import { FormSettings } from '../../interfaces/forms';

@Component({
  selector: 'oca-form-list-page',
  template: `
    <ng-container *ngIf="forms$ | async as forms">
      <oca-forms-list [forms]="forms"
                      [integrations]="integrations$ | async"
                      (createForm)="createForm()"
                      (deleteForm)="deleteForm($event)"></oca-forms-list>
      <div class="fab-bottom-right">
        <button type="button" mat-fab (click)="createForm()">
          <mat-icon>add</mat-icon>
        </button>
      </div>
    </ng-container>`,
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormListPageComponent implements OnInit {
  creating = false;
  forms$: Observable<Loadable<FormSettings[]>>;
  integrations$: Observable<NonNullLoadable<FormIntegrationConfiguration[]>>;

  constructor(private _store: Store<FormsState>,
              private _matDialog: MatDialog,
              private _translate: TranslateService) {
  }

  ngOnInit() {
    this._store.dispatch(new GetFormsAction());
    this.integrations$ = this._store.pipe(select(getIntegrations));
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
        title: this._translate.instant('oca.Confirm'),
        message: this._translate.instant('oca.confirm_delete_form'),
        ok: this._translate.instant('oca.Yes'),
        cancel: this._translate.instant('oca.Cancel'),
      },
    };
    this._matDialog.open(SimpleDialogComponent, config).afterClosed().subscribe((result: SimpleDialogResult) => {
      if (result && result.submitted) {
        this._store.dispatch(new DeleteFormAction(form));
      }
    });
  }
}
