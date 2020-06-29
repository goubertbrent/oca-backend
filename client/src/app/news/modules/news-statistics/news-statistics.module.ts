import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../../shared/shared.module';
import { NewsStatisticsGraphsComponent } from './components/news-statistics-graphs/news-statistics-graphs.component';
import { NewsStatisticsPageComponent } from './components/news-statistics-page.component';

const routes: Routes = [
  { path: '', component: NewsStatisticsPageComponent },
];

@NgModule({
  declarations: [ NewsStatisticsPageComponent, NewsStatisticsGraphsComponent ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    MatFormFieldModule,
    MatSelectModule,
    SharedModule,
    MatChipsModule,
  ],
  exports: [ NewsStatisticsPageComponent, NewsStatisticsGraphsComponent ],
})
export class NewsStatisticsModule {
}
