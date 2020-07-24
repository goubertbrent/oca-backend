import { ClipboardModule } from '@angular/cdk/clipboard';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { ErrorHandlingModule, MarkdownModule } from '@oca/web-shared';
import { ERROR_HANDLING_TRANLATIONS_PROVIDER } from '../../environments/config';
import { NewsItemPageComponent } from './news-item-page/news-item-page.component';
import { NewsEffects } from './news.effects';
import * as fromNews from './reducers';
import { MiddleclickDirective } from './middleclick.directive';


const routes: Routes = [
  { path: 'id/:newsId', component: NewsItemPageComponent },
];

@NgModule({
  declarations: [NewsItemPageComponent, MiddleclickDirective],
  imports: [
    MatToolbarModule,
    MatProgressBarModule,
    CommonModule,
    HttpClientModule,
    RouterModule.forChild(routes),
    TranslateModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MarkdownModule,
    StoreModule.forFeature(fromNews.newsFeatureKey, fromNews.newsReducer),
    EffectsModule.forFeature([NewsEffects]),
    ErrorHandlingModule,
    ClipboardModule,
  ],
  providers: [
    ERROR_HANDLING_TRANLATIONS_PROVIDER,
  ],
})
export class NewsModule {
}
