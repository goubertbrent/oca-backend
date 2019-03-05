import { Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { GetFormsAction } from '../forms/forms.actions';
import { FormsState, getForms } from '../forms/forms.state';
import { DynamicForm } from '../interfaces/forms.interfaces';
import { Loadable } from '../interfaces/loadable';

@Component({
  selector: 'oca-form-list-page',
  template: `
    <oca-forms-list [forms]="forms$ | async"></oca-forms-list>
    <div *ngIf="(forms$ | async).data?.length === 0">
      <p>{{ 'oca.no_forms_yet' | translate }}</p>
      <a mat-raised-button [routerLink]="['create']">{{ 'oca.create_form' | translate }}</a>
    </div>
    <div class="fab-bottom-right">
      <a mat-fab [routerLink]="['create']">
        <mat-icon>add</mat-icon>
      </a>
    </div>`,
})
export class FormListPageComponent implements OnInit {

  forms$: Observable<Loadable<DynamicForm[]>>;

  constructor(private store: Store<FormsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetFormsAction());
    this.forms$ = this.store.pipe(select(getForms));
  }

}
