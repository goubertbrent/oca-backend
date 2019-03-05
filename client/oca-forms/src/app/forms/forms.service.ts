import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CreateDynamicForm, DynamicForm, FormStatistics, OcaForm } from '../interfaces/forms.interfaces';
import { UserDetailsTO } from '../users/interfaces';

@Injectable({ providedIn: 'root' })
export class FormsService {

  getForms() {
    return this.http.get<DynamicForm[]>('/common/forms');
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

  constructor(private http: HttpClient) {
  }

  getTombolaWinners(formId: number) {
    return this.http.get <UserDetailsTO[ ]>(`/common/forms/${formId}/tombola/winners`);
  }
}
