import { HttpClient, HttpEvent, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { first, map } from 'rxjs/operators';
import { FormComponentType } from '../interfaces/enums';
import {
  CompletedFormStepType,
  CreateDynamicForm,
  FormSettings,
  FormStatistics,
  OcaForm,
  SingleSelectComponent,
  UploadedFile,
  UploadedFormFile,
} from '../interfaces/forms.interfaces';
import { UserDetailsTO } from '../users/interfaces';

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

  createForm(form: OcaForm<CreateDynamicForm>) {
    return this.http.post<OcaForm>(`/common/forms`, form);
  }

  getTombolaWinners(formId: number) {
    return this.http.get <UserDetailsTO[ ]>(`/common/forms/${formId}/tombola/winners`);
  }

  getDefaultForm(): Observable<OcaForm<CreateDynamicForm>> {
    const keys = [ 'oca.untitled_form', 'oca.untitled_section', 'oca.option_x', 'oca.untitled_question', 'oca.thank_you',
      'oca.your_response_has_been_recorded', 'oca.default_entry_section_text', 'oca.start' ];
    return this.translate.get(keys, { number: 1 }).pipe(
      first(),
      map(results => ({
        form: {
          title: results[ 'oca.untitled_form' ],
          max_submissions: -1,
          sections: [ {
            id: '0',
            title: results[ 'oca.untitled_section' ],
            description: results['oca.default_entry_section_text'],
            branding: null,
            components: [],
            next_button_caption: results['oca.start'],
          } , {
            id: '1',
            title: results[ 'oca.untitled_section' ],
            description: null,
            branding: null,
            components: [ {
              type: FormComponentType.SINGLE_SELECT,
              id: results[ 'oca.untitled_question' ],
              title: results[ 'oca.untitled_question' ],
              validators: [],
              choices: [ {
                label: results[ 'oca.option_x' ],
                value: results[ 'oca.option_x' ],
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
        },
      })));
  }

  deleteAllResponses(formId: number) {
    return this.http.delete(`/common/forms/${formId}/submissions`);
  }

  uploadImage(formId: number, image: Blob): Observable<HttpEvent<UploadedFormFile>> {
    const data = new FormData();
    data.append('file', image);
    return this.http.request(new HttpRequest('POST', `/common/forms/${formId}/image`, data, { reportProgress: true }));
  }

  getImages() {
    return this.http.get<UploadedFile[]>(`/common/images/forms`);
  }
}
