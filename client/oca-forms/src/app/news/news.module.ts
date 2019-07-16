import { FitBoundsService } from '@agm/core/services/fit-bounds';
import { DatePipe } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatBadgeModule } from '@angular/material/badge';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatRadioModule } from '@angular/material/radio';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatStepperIntl, MatStepperModule } from '@angular/material/stepper';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { Store, StoreModule } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { MatStepperIntlImpl } from '../forms/mat-stepper-intl-impl';
import { DateTimeInputModule } from '../shared/date-time-input/date-time-input.module';
import { SharedModule } from '../shared/shared.module';
import { UploadFileModule } from '../shared/upload-file';
import { ChooseLocationComponent } from './components/choose-location/choose-location.component';
import { ChooseRegionComponent } from './components/choose-region-dialog/choose-region.component';
import { EditNewsComponent } from './components/edit-news/edit-news.component';
import { NewsAppMapPickerDialogComponent } from './components/news-app-map-picker-dialog/news-app-map-picker-dialog.component';
import { NewsAppMapPickerComponent } from './components/news-app-map-picker/news-app-map-picker.component';
import { NewsItemListComponent } from './components/news-item-list/news-item-list.component';
import { NewsItemPreviewItemComponent } from './components/news-item-preview-item/news-item-preview-item.component';
import { NewsItemPreviewComponent } from './components/news-item-preview/news-item-preview.component';
import { NewsLocationComponent } from './components/news-location/news-location.component';
import { routes } from './news-routes';
import { GetNewsOptionsAction } from './news.actions';
import { NewsEffects } from './news.effects';
import { newsReducer } from './news.reducer';
import { NewsState } from './news.state';
import { CreateNewsPageComponent } from './pages/create-news-page/create-news-page.component';
import { EditNewsPageComponent } from './pages/edit-news-page/edit-news-page.component';
import { NewsDetailPageComponent } from './pages/news-detail-page/news-detail-page.component';
import { NewsListPageComponent } from './pages/news-list-page/news-list-page.component';

@NgModule({
  declarations: [
    NewsListPageComponent,
    NewsItemListComponent,
    EditNewsPageComponent,
    EditNewsComponent,
    NewsItemPreviewComponent,
    NewsDetailPageComponent,
    CreateNewsPageComponent,
    NewsLocationComponent,
    ChooseLocationComponent,
    ChooseRegionComponent,
    NewsItemPreviewItemComponent,
    NewsAppMapPickerComponent,
    NewsAppMapPickerDialogComponent,
  ],
  imports: [
    SharedModule,
    RouterModule.forChild(routes),
    EffectsModule.forFeature([NewsEffects]),
    StoreModule.forFeature('news', newsReducer),
    UploadFileModule,
    MatBadgeModule,
    MatChipsModule,
    MatStepperModule,
    MatRadioModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatToolbarModule,
    MatSnackBarModule,
    DateTimeInputModule,
    MatTooltipModule,
  ],
  providers: [
    { provide: MatStepperIntl, useClass: MatStepperIntlImpl, deps: [ TranslateService ] },
    FitBoundsService,
    DatePipe,
  ],
  entryComponents: [
    NewsAppMapPickerDialogComponent,
  ],
})
export class NewsModule {
  constructor(private _store: Store<NewsState>) {
    this._store.dispatch(new GetNewsOptionsAction());
  }
}
