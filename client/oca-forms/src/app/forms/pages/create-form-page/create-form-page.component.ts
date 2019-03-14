import { Component } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { CreateDynamicForm, OcaForm } from '../../../interfaces/forms.interfaces';
import { CreateFormAction } from '../../forms.actions';
import { FormsService } from '../../forms.service';
import { FormsState } from '../../forms.state';

@Component({
  selector: 'oca-create-form-page',
  template: `
    <mat-toolbar color="primary">
      <button mat-icon-button [routerLink]="['..']">
        <mat-icon>arrow_back</mat-icon>
      </button>
      <h1>{{ 'oca.create_form' | translate }}</h1>
    </mat-toolbar>
    <oca-edit-form [form]="form" (create)="onCreate($event)" *ngIf="form$ | async as form"></oca-edit-form>`,
})
export class CreateFormPageComponent {
  form$: Observable<OcaForm<CreateDynamicForm>>;

  constructor(private formsService: FormsService, private store: Store<FormsState>) {
    this.form$ = formsService.getDefaultForm();
  }

  onCreate(form: OcaForm<CreateDynamicForm>) {
    this.store.dispatch(new CreateFormAction(form));
  }

}
