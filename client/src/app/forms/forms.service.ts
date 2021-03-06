import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { first, map, switchMap } from 'rxjs/operators';
import { UserDetailsTO } from '../shared/users/users';
import { FormIntegrationConfiguration, TOPDeskCategory, TOPDeskSubCategory } from './integrations/integrations';
import { FormComponentType } from './interfaces/enums';
import {
  CompletedFormStepType,
  CreateDynamicForm,
  DownloadResponses,
  FormResponses,
  FormSettings,
  FormStatistics,
  LoadResponses,
  OcaForm,
  SingleSelectComponent,
} from './interfaces/forms';
import { FormValidatorType } from './interfaces/validators';
import { generateNewId } from './util';

@Injectable({ providedIn: 'root' })
export class FormsService {

  constructor(private http: HttpClient, private translate: TranslateService) {
  }

  getForms() {
    return this.http.get<FormSettings[]>('/common/forms');
  }

  getForm(formId: number) {
    return this.http.get<OcaForm>(`/common/forms/${formId}`);
  }

  getFormStatistics(formId: number) {
    return this.http.get<FormStatistics>(`/common/forms/${formId}/statistics`);
  }

  saveForm(form: OcaForm) {
    return this.http.put<OcaForm>(`/common/forms/${form.form.id}`, form);
  }

  testForm(formId: number, testers: string[]) {
    return this.http.post(`/common/forms/${formId}/test`, { testers });
  }

  createForm() {
    return this.getDefaultForm().pipe(switchMap(form => this.http.post<OcaForm>(`/common/forms`, form)));
  }


  copyForm(form: OcaForm) {
    form = { ...form, settings: { ...form.settings, steps: [], visible_until: null, finished: false, visible: false, tombola: null } };
    return this.http.post<OcaForm>(`/common/forms`, form);
  }

  getTombolaWinners(formId: number) {
    return this.http.get <UserDetailsTO[ ]>(`/common/forms/${formId}/tombola/winners`);
  }

  getResponses(payload: LoadResponses) {
    let params = new HttpParams();
    params = params.set('page_size', payload.page_size.toString());
    if (payload.cursor) {
      params = params.set('cursor', payload.cursor);
    }
    return this.http.get<FormResponses>(`/common/forms/${payload.formId}/submissions`, { params });
  }

  deleteResponse(formId: number, responseId: number) {
    return this.http.delete(`/common/forms/${formId}/submissions/${responseId}`);
  }

  deleteAllResponses(formId: number) {
    return this.http.delete(`/common/forms/${formId}/submissions`);
  }

  deleteForm(formId: number) {
    return this.http.delete(`/common/forms/${formId}`);
  }

  getIntegrations() {
    return this.http.get<FormIntegrationConfiguration[]>(`/common/forms/integrations`);
  }

  getTOPDeskCategories() {
    return this.http.get<TOPDeskCategory[]>(`/common/forms/integrations/topdesk/categories`);
  }

  getTOPDeskSubCategories() {
    return this.http.get<TOPDeskSubCategory[]>(`/common/forms/integrations/topdesk/subcategories`);
  }

  updateIntegration(data: FormIntegrationConfiguration) {
    return this.http.put<FormIntegrationConfiguration>(`/common/forms/integrations/${data.provider}`, data);
  }

  downloadResponses(id: number) {
    return this.http.get<DownloadResponses>(`/common/forms/${id}/export`);
  }

  private getDefaultForm(): Observable<OcaForm<CreateDynamicForm>> {
    const keys = [ 'oca.untitled_form', 'oca.untitled_section', 'oca.option_x', 'oca.untitled_question', 'oca.thank_you',
      'oca.your_response_has_been_recorded', 'oca.default_entry_section_text', 'oca.start' ];
    return this.translate.get(keys, { number: 1 }).pipe(
      first(),
      map(results => ({
        form: {
          title: results[ 'oca.untitled_form' ],
          max_submissions: 1,
          sections: [ {
            id: '0',
            title: results[ 'oca.untitled_section' ],
            description: results[ 'oca.default_entry_section_text' ],
            branding: null,
            next_action: null,
            components: [],
            next_button_caption: results[ 'oca.start' ],
          }, {
            id: '1',
            title: results[ 'oca.untitled_section' ],
            description: null,
            branding: null,
            next_action: null,
            components: [ {
              type: FormComponentType.SINGLE_SELECT,
              id: generateNewId(),
              title: results[ 'oca.untitled_question' ],
              validators: [ { type: FormValidatorType.REQUIRED } ],
              choices: [ {
                label: results[ 'oca.option_x' ],
                value: generateNewId(),
              } ],
              description: null,
            } as SingleSelectComponent ],
          } ],
          submission_section: {
            title: results[ 'oca.thank_you' ],
            description: results[ 'oca.your_response_has_been_recorded' ],
            components: [],
            branding: null,
          },
        },
        settings: {
          title: results[ 'oca.untitled_form' ],
          visible: false,
          visible_until: null,
          finished: false,
          tombola: null,
          id: 0,
          steps: [ { step_id: CompletedFormStepType.CONTENT } ],
          integrations: [],
        },
      })));
  }
}
