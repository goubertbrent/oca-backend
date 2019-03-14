import { Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { FormSettings } from '../../../interfaces/forms.interfaces';
import { Loadable } from '../../../interfaces/loadable';
import { GetFormsAction } from '../../forms.actions';
import { FormsState, getForms } from '../../forms.state';

@Component({
  selector: 'oca-form-list-page',
  template: `
    <ng-container *ngIf="forms$ | async as forms">
      <oca-forms-list [forms]="forms"></oca-forms-list>
      <div class="fab-bottom-right">
        <a mat-fab [routerLink]="['create']">
          <mat-icon>add</mat-icon>
        </a>
      </div>
    </ng-container>`,
})
export class FormListPageComponent implements OnInit {

  forms$: Observable<Loadable<FormSettings[]>>;

  constructor(private store: Store<FormsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetFormsAction());
    this.forms$ = this.store.pipe(select(getForms));
  }

}
