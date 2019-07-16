import { Routes } from '@angular/router';
import { CreateNewsPageComponent } from './pages/create-news-page/create-news-page.component';
import { EditNewsPageComponent } from './pages/edit-news-page/edit-news-page.component';
import { NewsDetailPageComponent } from './pages/news-detail-page/news-detail-page.component';
import { NewsListPageComponent } from './pages/news-list-page/news-list-page.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'create' },
  { path: 'list', component: NewsListPageComponent },
  { path: 'create', component: CreateNewsPageComponent },
  {
    path: 'details/:id', component: NewsDetailPageComponent, children: [
      { path: '', redirectTo: 'edit', pathMatch: 'full' },
      { path: 'edit', component: EditNewsPageComponent },
      {
        path: 'statistics',
        loadChildren: () => import('./modules/news-statistics/news-statistics.module').then(m => m.NewsStatisticsModule),
      },
    ],
  },
];
