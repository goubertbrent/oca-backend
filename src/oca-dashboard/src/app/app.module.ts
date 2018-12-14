import { HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import {
  MatButtonModule,
  MatExpansionModule,
  MatIconModule,
  MatLineModule,
  MatListModule,
  MatSidenavModule,
  MatToolbarModule,
} from '@angular/material';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateLoader, TranslateModule } from '@ngx-translate/core';

import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { CreateNewsPageComponent } from './create-news-page/create-news-page.component';
import { HomePageComponent } from './home-page/home-page.component';
import { NavItemComponent } from './nav-item/nav-item.component';
import { NewsListPageComponent } from './news-list-page/news-list-page.component';

const MATERIAL_MODULES = [
  MatButtonModule,
  MatExpansionModule,
  MatIconModule,
  MatLineModule,
  MatListModule,
  MatSidenavModule,
  MatToolbarModule,
];

export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http);
}

@NgModule({
  declarations: [
    AppComponent,
    HomePageComponent,
    NavItemComponent,
    CreateNewsPageComponent,
    NewsListPageComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    HttpClientModule,
    TranslateModule.forRoot({
        loader: {
          provide: TranslateLoader,
          useFactory: HttpLoaderFactory,
          deps: [ HttpClient ],
        },
      },
    ),
    FlexLayoutModule,
    MATERIAL_MODULES,
  ],
  providers: [],
  bootstrap: [ AppComponent ],
})
export class AppModule {
}
