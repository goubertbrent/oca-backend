import { Routes } from '@angular/router';
import { CreateFormPageComponent } from './forms/pages/create-form-page/create-form-page.component';
import { FormDetailsPageComponent } from './forms/pages/form-details-page/form-details-page.component';
import { FormListPageComponent } from './forms/pages/form-list-page/form-list-page.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: '/forms' },
  { path: 'forms', component: FormListPageComponent },
  { path: 'forms/create', component: CreateFormPageComponent },
  { path: 'forms/:id', component: FormDetailsPageComponent },
];
