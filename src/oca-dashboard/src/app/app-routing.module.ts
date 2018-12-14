import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CreateNewsPageComponent } from './create-news-page/create-news-page.component';
import { HomePageComponent } from './home-page/home-page.component';
import { NewsListPageComponent } from './news-list-page/news-list-page.component';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'home',
    component: HomePageComponent,
  },
  {
    path: 'news',
    redirectTo: 'news/list',
    pathMatch: 'full',
  },
  {
    path: 'news/list',
    component: NewsListPageComponent,
  },
  {
    path: 'news/create',
    component: CreateNewsPageComponent,
  },
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ],
})
export class AppRoutingModule {
}
