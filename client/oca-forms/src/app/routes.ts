import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: '/forms' },
  { path: 'news', loadChildren: './news/news.module#NewsModule' },
  { path: 'forms', loadChildren: './forms/oca-forms.module#OcaFormsModule' },
];
