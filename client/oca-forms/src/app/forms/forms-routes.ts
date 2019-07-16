import { Routes } from '@angular/router';
import { FormDetailsPageComponent } from './pages/form-details-page/form-details-page.component';
import { FormListPageComponent } from './pages/form-list-page/form-list-page.component';

export const routes: Routes = [
  { path: '', component: FormListPageComponent },
  { path: ':id', component: FormDetailsPageComponent },
];
