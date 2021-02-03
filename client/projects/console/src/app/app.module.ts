import { CommonModule, DatePipe } from '@angular/common';
import { HttpClientJsonpModule, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { FlexLayoutModule, SERVER_TOKEN } from '@angular/flex-layout';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule, MatIconRegistry } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { Store, StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { MissingTranslationHandler, MissingTranslationHandlerParams, TranslateModule, TranslateService } from '@ngx-translate/core';
import { ColorPickerModule } from 'ngx-color-picker';
import { environment } from '../../../../src/environments/environment';
import { NavModule } from '../../framework/client/nav/nav.module';
import { AddRoutesAction } from '../../framework/client/nav/sidebar';
import { rcc as englishTranslations } from '../assets/i18n/en.json';
import { AppComponent } from './app.component';
import {
  AdminServicesComponent,
  ApiRequestStatusComponent,
  AppAdvancedConfigurationComponent,
  AppAdvancedConfigurationFormComponent,
  AppAPNsIosComponent,
  AppAssetListComponent,
  AppAssetsOverviewComponent,
  AppBasicConfigurationComponent,
  AppBasicConfigurationFormComponent,
  AppBrandingComponent,
  AppConfigurationComponent,
  AppDefaultBrandingsComponent,
  AppDetailComponent,
  AppearanceColorsComponent,
  AppearanceComponent,
  AppearanceEditImageComponent,
  AppearanceEditImageFormComponent,
  AppearanceGenerateImagesComponent,
  AppearanceGenerateImagesFormComponent,
  AppearanceImagesComponent,
  AppearanceSidebarComponent,
  AppListComponent,
  AppListPageComponent,
  AppResourceComponent,
  AppResourcesComponent,
  AppsComponent,
  AppSettingsComponent,
  AppSettingsFirebaseIosComponent,
  AppSettingsFormComponent,
  AutoAddedServiceDialogComponent,
  BackendBrandingsComponent,
  BackendDefaultAppComponent,
  BackendDefaultSettingsComponent,
  BackendDefaultSettingsOverviewComponent,
  BackendResourcesComponent,
  BuildCreateComponent,
  BuildListComponent,
  BuildSettingsComponent,
  BuildSettingsFormComponent,
  BulkUpdateComponent,
  BulkUpdateFormComponent,
  CheckListComponent,
  ColorsFormComponent,
  ContactsComponent,
  CoreBrandingComponent,
  CreateAppComponent,
  CreateAppResourceComponent,
  CreateContactComponent,
  CreateDefaultBrandingComponent,
  CreateDeveloperAccountComponent,
  CreateDeveloperAccountFormComponent,
  CreateEmbeddedAppPageComponent,
  CreateFirebaseProjectPageComponent,
  CreatePaymentProviderComponent,
  CreateQrCodeTemplateComponent,
  CreateReviewNotesComponent,
  DefaultBrandingListComponent,
  DeveloperAccountDetailsComponent,
  DeveloperAccountsComponent,
  EditBackendBrandingComponent,
  EditBackendResourceComponent,
  EditContactComponent,
  EditContactFormComponent,
  EditDeveloperAccountComponent,
  EditDeveloperAccountFormComponent,
  EditNavigationItemDialogComponent,
  EditPaymentProviderComponent,
  EditReviewNotesComponent,
  EditReviewNotesFormComponent,
  EmbeddedAppDetailComponent,
  EmbeddedAppsComponent,
  EmbeddedAppsListPageComponent,
  FirebaseProjectsComponent,
  FirebaseProjectsListPageComponent,
  HomePageComponent,
  NavigationCardsComponent,
  NavigationItemListComponent,
  NotFoundComponent,
  PaymentProviderFormComponent,
  PaymentProvidersComponent,
  PaymentProvidersListComponent,
  QrCodeTemplateComponent,
  QrCodeTemplateListComponent,
  QrCodeTemplatesComponent,
  ReviewNotesComponent,
  SidebarFormComponent,
  StoreListingConfigurationComponent,
  StoreListingDetailComponent,
  StoreListingDetailFormComponent,
  StoreListingTranslationsComponent,
  StoreListingTranslationsFormComponent,
  TranslationsEditorComponent,
  UpdateEmbeddedAppPageComponent,
} from './components';
import { consoleRoutes } from './console.routes';
import { AppsEffects, BackendsEffects, ContactsEffects, DeveloperAccountsEffects, ReviewNotesEffects } from './effects';
import { consoleReducers } from './reducers';
import {
  ApiErrorService,
  AppsService,
  ConsoleConfig,
  ContactsService,
  DeveloperAccountsService,
  ReviewNotesService,
  RogerthatBackendsService,
} from './services';

@Injectable()
export class MissingTranslationWarnHandler implements MissingTranslationHandler {

  handle(params: MissingTranslationHandlerParams) {
    const lang = params.translateService.currentLang;
    console.warn(`Missing translation for key '${params.key}' for language '${lang}'`);
    return params.key;
  }
}

@NgModule({
  bootstrap: [AppComponent],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    HttpClientJsonpModule,
    TranslateModule.forRoot({
      defaultLanguage: 'en',
      useDefaultLang: true,
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
    FlexLayoutModule,
    ColorPickerModule,
    RouterModule.forRoot(consoleRoutes),
    StoreModule.forRoot(consoleReducers, {
      runtimeChecks: {
        // TODO: enable
        strictStateSerializability: false,
        strictActionSerializability: false,
        strictStateImmutability: false,
        strictActionImmutability: false,
        strictActionWithinNgZone: true,
      },
    }),
    StoreDevtoolsModule.instrument({
      name: 'Our City App console',
      maxAge: 25,
      logOnly: environment.production,
    }),
    EffectsModule.forRoot([AppsEffects, BackendsEffects, DeveloperAccountsEffects, ReviewNotesEffects, ContactsEffects]),
    NavModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatRadioModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatTabsModule,
    MatToolbarModule,
    MatProgressSpinnerModule,
    MatExpansionModule,
    MatTableModule,
    MatDialogModule,
    MatSidenavModule,
  ],
  declarations: [
    AppComponent,
    AdminServicesComponent,
    ApiRequestStatusComponent,
    AppAPNsIosComponent,
    AppAdvancedConfigurationComponent,
    AppAdvancedConfigurationFormComponent,
    AppAssetListComponent,
    AppAssetsOverviewComponent,
    AppBasicConfigurationComponent,
    AppBasicConfigurationFormComponent,
    AppBrandingComponent,
    AppConfigurationComponent,
    AppDefaultBrandingsComponent,
    AppDetailComponent,
    AppearanceColorsComponent,
    AppearanceComponent,
    AppearanceEditImageComponent,
    AppearanceEditImageFormComponent,
    AppearanceGenerateImagesComponent,
    AppearanceGenerateImagesFormComponent,
    AppearanceImagesComponent,
    AppearanceSidebarComponent,
    AppListComponent,
    AppListPageComponent,
    AppResourceComponent,
    AppResourcesComponent,
    AppsComponent,
    AppSettingsComponent,
    AppSettingsFormComponent,
    AppSettingsFirebaseIosComponent,
    AutoAddedServiceDialogComponent,
    BackendBrandingsComponent,
    BackendDefaultAppComponent,
    BackendDefaultSettingsComponent,
    BackendDefaultSettingsOverviewComponent,
    BackendResourcesComponent,
    BuildCreateComponent,
    BuildListComponent,
    BuildSettingsComponent,
    BuildSettingsFormComponent,
    BulkUpdateComponent,
    BulkUpdateFormComponent,
    CheckListComponent,
    ColorsFormComponent,
    ContactsComponent,
    CoreBrandingComponent,
    CreateAppComponent,
    CreateAppResourceComponent,
    CreateContactComponent,
    CreateDefaultBrandingComponent,
    CreateDeveloperAccountComponent,
    CreateDeveloperAccountFormComponent,
    CreateEmbeddedAppPageComponent,
    CreatePaymentProviderComponent,
    CreateQrCodeTemplateComponent,
    CreateReviewNotesComponent,
    DefaultBrandingListComponent,
    DeveloperAccountDetailsComponent,
    DeveloperAccountsComponent,
    EditBackendBrandingComponent,
    EditBackendResourceComponent,
    EditContactComponent,
    EditContactFormComponent,
    EditDeveloperAccountComponent,
    EditDeveloperAccountFormComponent,
    EditNavigationItemDialogComponent,
    EditPaymentProviderComponent,
    EditReviewNotesComponent,
    EditReviewNotesFormComponent,
    EmbeddedAppDetailComponent,
    EmbeddedAppsComponent,
    EmbeddedAppsListPageComponent,
    FirebaseProjectsComponent,
    FirebaseProjectsListPageComponent,
    CreateFirebaseProjectPageComponent,
    HomePageComponent,
    NavigationCardsComponent,
    NavigationItemListComponent,
    NotFoundComponent,
    PaymentProviderFormComponent,
    PaymentProvidersComponent,
    PaymentProvidersListComponent,
    QrCodeTemplateComponent,
    QrCodeTemplateListComponent,
    QrCodeTemplatesComponent,
    ReviewNotesComponent,
    SidebarFormComponent,
    StoreListingConfigurationComponent,
    StoreListingDetailComponent,
    StoreListingDetailFormComponent,
    StoreListingTranslationsComponent,
    StoreListingTranslationsFormComponent,
    TranslationsEditorComponent,
    UpdateEmbeddedAppPageComponent,
  ],
  providers: [
    AppsService,
    ContactsService,
    DatePipe,
    DeveloperAccountsService,
    ReviewNotesService,
    RogerthatBackendsService,
    ConsoleConfig,
    ApiErrorService,
    {
      provide: SERVER_TOKEN,
      useValue: false,
    },
  ],
})

export class AppModule {

  constructor(private matIconRegistry: MatIconRegistry,
              private translate: TranslateService,
              private store: Store) {
    this.translate.use('en');
    matIconRegistry.registerFontClassAlias('fontawesome', 'fa');
    this.translate.setTranslation('en', { rcc: englishTranslations });
    this.store.dispatch(new AddRoutesAction(consoleRoutes));
  }
}
