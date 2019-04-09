import { NgModule } from '@angular/core';
import {
  MatBadgeModule,
  MatChipsModule,
  MatDatepickerModule,
  MatNativeDateModule,
  MatRadioModule,
  MatSelectModule,
  MatSlideToggleModule,
  MatStepperModule,
} from '@angular/material';
import { RouterModule } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { Store, StoreModule } from '@ngrx/store';
import { SharedModule } from '../shared/shared.module';
import { EditNewsComponent } from './components/edit-news/edit-news.component';
import { NewsItemListComponent } from './components/news-item-list/news-item-list.component';
import { routes } from './news-routes';
import { GetNewsOptionsAction } from './news.actions';
import { NewsEffects } from './news.effects';
import { newsReducer } from './news.reducer';
import { NewsState } from './news.state';
import { EditNewsPageComponent } from './pages/edit-news-page/edit-news-page.component';
import { NewsListPageComponent } from './pages/news-list-page/news-list-page.component';

@NgModule({
  declarations: [ NewsListPageComponent, NewsItemListComponent, EditNewsPageComponent, EditNewsComponent ],
  imports: [
    SharedModule,
    RouterModule.forChild(routes),
    EffectsModule.forFeature([ NewsEffects ]),
    StoreModule.forFeature('news', newsReducer),
    MatBadgeModule,
    MatChipsModule,
    MatStepperModule,
    MatRadioModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatDatepickerModule,
    MatNativeDateModule,
  ],
})
export class NewsModule {
  constructor(private _store: Store<NewsState>) {
    this._store.dispatch(new GetNewsOptionsAction());
  }
}
