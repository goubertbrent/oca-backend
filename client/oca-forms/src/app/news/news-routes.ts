import { Routes } from '@angular/router';
import { EditNewsPageComponent } from './pages/edit-news-page/edit-news-page.component';
import { NewsListPageComponent } from './pages/news-list-page/news-list-page.component';

export const routes: Routes = [
  { path: '', component: NewsListPageComponent },
  { path: '/create', component: EditNewsPageComponent },
  { path: ':id', component: EditNewsPageComponent },
];
