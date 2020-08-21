import { Route } from './app.routes';
import {
  AppAdvancedConfigurationComponent,
  AppAssetsOverviewComponent,
  AppBasicConfigurationComponent,
  AppConfigurationComponent,
  AppDefaultBrandingsComponent,
  AppDetailComponent,
  AppearanceColorsComponent,
  AppearanceComponent,
  AppearanceEditImageComponent,
  AppearanceGenerateImagesComponent,
  AppearanceImagesComponent,
  AppearanceSidebarComponent,
  AppListPageComponent,
  AppResourcesComponent,
  AppsComponent,
  AppSettingsComponent,
  AppSettingsFirebaseIosComponent,
  BackendBrandingsComponent,
  BackendDefaultAppComponent,
  BackendDefaultSettingsComponent,
  BackendDefaultSettingsOverviewComponent,
  BackendResourcesComponent,
  BuildCreateComponent,
  BuildListComponent,
  BuildSettingsComponent,
  BulkUpdateComponent,
  ContactsComponent,
  CoreBrandingComponent,
  CreateAppComponent,
  CreateAppResourceComponent,
  CreateContactComponent,
  CreateDefaultBrandingComponent,
  CreateDeveloperAccountComponent,
  CreateEmbeddedAppPageComponent,
  CreateFirebaseProjectPageComponent,
  CreatePaymentProviderComponent,
  CreateQrCodeTemplateComponent,
  CreateReviewNotesComponent,
  DeveloperAccountDetailsComponent,
  DeveloperAccountsComponent,
  EditBackendBrandingComponent,
  EditBackendResourceComponent,
  EditContactComponent,
  EditDeveloperAccountComponent,
  EditPaymentProviderComponent,
  EditReviewNotesComponent,
  EmbeddedAppsComponent,
  EmbeddedAppsListPageComponent,
  FirebaseProjectsComponent,
  FirebaseProjectsListPageComponent,
  HomePageComponent,
  NewsGroupComponent,
  NewsSettingsComponent,
  NotFoundComponent,
  PaymentProvidersComponent,
  PaymentProvidersListComponent,
  QrCodeTemplatesComponent,
  ReviewNotesComponent,
  StoreListingConfigurationComponent,
  StoreListingDetailComponent,
  StoreListingTranslationsComponent,
  UpdateEmbeddedAppPageComponent,
} from './components';

export const consoleRoutes: Array<Route> = [
  {
    path: '',
    data: {
      id: 'home',
      icon: 'home',
      label: 'rcc.home',

    },
    component: HomePageComponent,
  },
  {
    path: 'apps',
    data: {
      label: 'rcc.apps',
      icon: 'apps',
      id: 'apps',
      description: 'rcc.apps_explanation',
    },
    component: AppsComponent,
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      {
        path: 'overview',
        component: AppListPageComponent,
        data: { label: 'rcc.apps' },
      },
      {
        path: 'create',
        component: CreateAppComponent,
        data: { label: 'rcc.create' },
      },
      {
        path: 'bulk-update',
        component: BulkUpdateComponent,
        data: { label: 'rcc.bulk_update' },
      },
    ],
  },
  {
    path: 'apps/:appId',
    data: {
      label: 'rcc.apps',
      icon: 'apps',
    },
    component: AppDetailComponent,
    children: [
      { path: '', redirectTo: 'settings', pathMatch: 'full' },
      {
        path: 'settings',
        component: AppConfigurationComponent,
        children: [
          { path: '', redirectTo: 'basic', pathMatch: 'full' },
          {
            path: 'basic',
            component: AppBasicConfigurationComponent,
            data: { label: 'rcc.basic_app_settings' },
          },
          {
            path: 'build-settings',
            component: BuildSettingsComponent,
            data: { label: 'rcc.build_settings' },
          },
          {
            path: 'app-settings',
            component: AppSettingsComponent,
            data: { label: 'rcc.app_settings' },
          },
          {
            path: 'app-settings/firebase-ios',
            component: AppSettingsFirebaseIosComponent,
            data: { label: 'rcc.app_settings' },
          },
          {
            path: 'advanced',
            component: AppAdvancedConfigurationComponent,
            data: { label: 'rcc.advanced_app_settings' },
          },
          {
            path: 'news',
            component: NewsSettingsComponent,
            data: { label: 'rcc.news_settings' },
          },
          {
            path: 'news/:groupId',
            component: NewsGroupComponent,
            data: { label: 'rcc.news_settings' },
          },
        ],
      },
      { path: 'assets', component: AppAssetsOverviewComponent, data: { label: 'rcc.assets' } },
      {
        path: 'assets/core-branding',
        component: CoreBrandingComponent,
        data: { label: 'rcc.core_branding' },
      },
      {
        path: 'assets/qr-code-templates/create',
        component: CreateQrCodeTemplateComponent,
        data: { label: 'rcc.create_qr_code_template' },
      },
      {
        path: 'assets/qr-code-templates',
        component: QrCodeTemplatesComponent,
        data: { label: 'rcc.qr_code_templates' },
      },
      {
        path: 'assets/resources/create',
        component: CreateAppResourceComponent,
        data: { label: 'rcc.create_resource' },
      },
      { path: 'assets/resources', component: AppResourcesComponent, data: { label: 'rcc.resources' } },
      {
        path: 'assets/brandings/create',
        component: CreateDefaultBrandingComponent,
        data: { label: 'rcc.create_branding' },
      },
      { path: 'assets/brandings', component: AppDefaultBrandingsComponent, data: { label: 'rcc.brandings' } },
      { path: 'builds', component: BuildListComponent, data: { label: 'rcc.builds' } },
      { path: 'builds/create', component: BuildCreateComponent, data: { label: 'rcc.create_build' } },
      {
        path: 'store-listing',
        component: StoreListingConfigurationComponent,
        children: [
          { path: '', redirectTo: 'general', pathMatch: 'full' },
          {
            path: 'general',
            component: StoreListingDetailComponent,
            data: { label: 'rcc.general_information' },
          },
          {
            path: 'translations',
            component: StoreListingTranslationsComponent,
            data: { label: 'rcc.translations' },
          }],
      },
      {
        path: 'appearance',
        component: AppearanceComponent,
        children: [
          { path: '', redirectTo: 'colors', pathMatch: 'full' },
          { path: 'colors', component: AppearanceColorsComponent, data: { label: 'rcc.color' } },
          { path: 'sidebar', component: AppearanceSidebarComponent, data: { label: 'rcc.sidebar' } },
          {
            path: 'images',
            component: AppearanceImagesComponent,
            data: { label: 'rcc.images' },
          },
          {
            path: 'images/generate',
            component: AppearanceGenerateImagesComponent,
            data: { label: 'rcc.generate' },
          },
          {
            path: 'images/:imageType',
            component: AppearanceEditImageComponent,
            data: { label: 'rcc.edit_image' },
          },
        ],
      },
    ],
  },
  {
    path: 'default-settings',
    component: BackendDefaultSettingsComponent,
    data: {
      label: 'rcc.default_settings',
      icon: 'settings',
      id: 'default_settings',
    },
    children: [
      {
        path: '',
        component: BackendDefaultSettingsOverviewComponent,
        data: { label: 'rcc.default_settings' },
      },
      { path: 'app', component: BackendDefaultAppComponent, data: { label: 'rcc.set_default_app' } },
      {
        path: 'resources',
        component: BackendResourcesComponent,
        data: { label: 'rcc.backend_resources' },
      },
      {
        path: 'resources/create',
        component: EditBackendResourceComponent,
        data: { label: 'rcc.create_backend_resource' },
      },
      {
        path: 'resources/:resourceId',
        component: EditBackendResourceComponent,
        data: { label: 'rcc.edit_backend_resource' },
      },
      {
        path: 'brandings',
        component: BackendBrandingsComponent,
        data: { label: 'rcc.backend_brandings' },
      },
      {
        path: 'brandings/create',
        component: EditBackendBrandingComponent,
        data: { label: 'rcc.create_backend_branding' },
      },
      {
        path: 'brandings/:brandingId',
        component: EditBackendBrandingComponent,
        data: { label: 'rcc.edit_backend_branding' },
      },
    ],
  },
  {
    path: 'payment-providers',
    component: PaymentProvidersComponent,
    data: {
      label: 'rcc.payment_providers',
      icon: 'attach_money',
      id: 'payment_providers',
    },
    children: [{
      path: '',
      component: PaymentProvidersListComponent,
      data: { label: 'rcc.payment_providers' },
    }, {
      path: 'create',
      component: CreatePaymentProviderComponent,
      data: { label: 'rcc.create_payment_provider' },
    }, {
      path: ':paymentProviderId',
      component: EditPaymentProviderComponent,
      data: { label: 'rcc.payment_provider' },
    }],
  },
  {
    path: 'embedded-apps',
    component: EmbeddedAppsComponent,
    data: {
      label: 'rcc.embedded_apps',
      icon: 'apps',
      id: 'embedded_apps',
    },
    children: [{
      path: '',
      component: EmbeddedAppsListPageComponent,
      data: { label: 'rcc.embedded_apps' },
    }, {
      path: 'create',
      component: CreateEmbeddedAppPageComponent,
      data: { label: 'rcc.create_embedded_app' },
    }, {
      path: ':embeddedAppId',
      component: UpdateEmbeddedAppPageComponent,
      data: { label: 'rcc.update_embedded_app' },
    }],
  },
  {
    path: 'firebase-projects',
    component: FirebaseProjectsComponent,
    data: {
      label: 'rcc.firebase_projects',
      icon: 'apps',
      id: 'firebase_projects',
    },
    children: [{
      path: '',
      component: FirebaseProjectsListPageComponent,
      data: { label: 'rcc.firebase_projects' },
    }, {
      path: 'create',
      component: CreateFirebaseProjectPageComponent,
      data: { label: 'rcc.create_firebase_project' },
    }],
  },
  {
    path: 'developer-accounts',
    data: {
      label: 'rcc.developer_accounts',
      id: 'developer_accounts',
      description: 'rcc.developer_accounts_explanation',
      icon: 'account_box',
    },
    component: DeveloperAccountsComponent,
  },
  {
    path: 'developer-accounts/create',
    data: {
      label: 'rcc.create_developer_account',
    },
    component: CreateDeveloperAccountComponent,
  },
  {
    path: 'developer-accounts/:accountId',
    component: DeveloperAccountDetailsComponent,
    children: [
      { path: '', redirectTo: 'details', pathMatch: 'full' },
      {
        path: 'details',
        component: EditDeveloperAccountComponent,
        data: { label: 'rcc.developer_account_details' },
      },
    ],
  },
  {
    path: 'contacts',
    component: ContactsComponent,
    data: {
      label: 'rcc.contacts',
      id: 'contacts',
      description: 'rcc.contacts_explanation',
      icon: 'contacts',
    },
  }, {
    path: 'contacts/create',
    component: CreateContactComponent,
    data: { label: 'rcc.create_contact' },
  }, {
    path: 'contacts/:contactId',
    component: EditContactComponent,
    data: { label: 'rcc.edit_contact' },
  },
  {
    path: 'review-notes',
    component: ReviewNotesComponent,
    data: {
      label: 'rcc.review_notes',
      id: 'review_notes',
      description: 'rcc.review_notes_explanation',
      icon: 'note',
    },
  }, {
    path: 'review-notes/create',
    component: CreateReviewNotesComponent,
    data: { label: 'rcc.create_review_notes' },
  }, {
    path: 'review-notes/:reviewNotesId',
    component: EditReviewNotesComponent,
    data: { label: 'rcc.edit_review_notes' },
  },
  {
    path: '**',
    data: {
      label: {
        title: 'Page not found',
      },
    },
    component: NotFoundComponent,
  },
];
