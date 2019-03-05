import { Component } from '@angular/core';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CreateFormAction } from '../forms/forms.actions';
import { FormsState } from '../forms/forms.state';
import { FormComponentType } from '../interfaces/enums';
import { CreateDynamicForm, OcaForm, SingleSelectComponent } from '../interfaces/forms.interfaces';

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

  constructor(private translate: TranslateService, private store: Store<FormsState>) {
    this.form$ = this.translate.get([ 'oca.untitled_form', 'oca.untitled_section', 'oca.option_x' ], { number: 1 }).pipe(
      map(results => ({
        form: {
          title: results[ 'oca.untitled_form' ],
          max_submissions: -1,
          sections: [ {
            id: '0',
            title: results[ 'oca.untitled_section' ],
            description: null,
            components: [ {
              type: FormComponentType.SINGLE_SELECT,
              id: '',
              title: '',
              validators: [],
              choices: [ {
                label: results[ 'oca.option_x' ],
                value: results[ 'oca.option_x' ],
              } ],
              description: null,
            } as SingleSelectComponent ],
          } ],
          submission_section: null,
        },
        settings: {
          visible: false,
          visible_until: null,
          finished: false,
          tombola: null,
          id: 0,
        },
      })));
  }

  onCreate(form: OcaForm<CreateDynamicForm>) {
    this.store.dispatch(new CreateFormAction(form));
  }

}
