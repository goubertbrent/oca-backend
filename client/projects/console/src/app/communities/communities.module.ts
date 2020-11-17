import { DragDropModule } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { ErrorHandlingModule } from '@oca/web-shared';
import { NavModule } from '../../../framework/client/nav/nav.module';
import { CommunitiesEffects } from './communities.effects';
import { communitiesReducer, communityFeatureKey } from './community.reducer';
import { AutoConnectedServicesComponent } from './community/auto-connected-services/auto-connected-services.component';
import { CommunitiesListComponent } from './community/communities-list/communities-list.component';
import { CommunityDetailComponent } from './community/community-detail/community-detail.component';
import { CommunityFormComponent } from './community/community-form/community-form.component';
import { CreateCommunityComponent } from './community/create-community/create-community.component';
import { EditAutoConnectedServiceDialogComponent } from './community/edit-acs-dialog/edit-acs-dialog.component';
import { EditCommunityComponent } from './community/edit-community/edit-community.component';
import { AddTranslationDialogComponent } from './homescreen/add-translation-dialog/add-translation-dialog.component';
import { AppActionEditorComponent } from './homescreen/app-action-editor/app-action-editor.component';
import { EditListItemTemplateComponent } from './homescreen/edit-list-item-template/edit-list-item-template.component';
import { HomeScreenBottomNavigationComponent } from './homescreen/home-screen-bottom-navigation/home-screen-bottom-navigation.component';
import { HomeScreenBottomSheetComponent } from './homescreen/home-screen-bottom-sheet/home-screen-bottom-sheet.component';
import { HomeScreenFormComponent } from './homescreen/home-screen-form/home-screen-form.component';
import { HomeScreenPageComponent } from './homescreen/home-screen-page/home-screen-page.component';
import { HomeScreenTranslationsEditorComponent } from './homescreen/home-screen-translations-editor/home-screen-translations-editor.component';
import { NewsGroupFormComponent } from './news/news-group-form/news-group-form.component';
import { NewsGroupComponent } from './news/news-group/news-group.component';
import { NewsSettingsComponent } from './news/news-setings/news-settings.component';
import { IconSelectorComponent } from './homescreen/icon-selector/icon-selector.component';
import { LinkItemTemplateContentEditorComponent } from './homescreen/link-item-template-content-editor/link-item-template-content-editor.component';
import { HomeScreenTranslationSelectComponent } from './homescreen/home-screen-translation-select/home-screen-translation-select.component';

const routes: Routes = [
  { path: '', component: CommunitiesListComponent },
  { path: 'create', component: CreateCommunityComponent },
  {
    path: ':communityId',
    component: CommunityDetailComponent,
    children: [
      { path: '', redirectTo: 'settings', pathMatch: 'full' },
      { path: 'settings', component: EditCommunityComponent },
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
      { path: 'home-screen', redirectTo: 'home-screen/default', pathMatch: 'full' },
      {
        path: 'home-screen/:homeScreenId',
        component: HomeScreenPageComponent,
        data: { label: 'rcc.homescreen' },
      },
    ],
  },
];

@NgModule({
  declarations: [
    CommunitiesListComponent,
    EditCommunityComponent,
    AutoConnectedServicesComponent,
    EditAutoConnectedServiceDialogComponent,
    CommunityDetailComponent,
    NewsGroupFormComponent,
    NewsGroupComponent,
    NewsSettingsComponent,
    CreateCommunityComponent,
    CommunityFormComponent,
    HomeScreenPageComponent,
    HomeScreenFormComponent,
    AppActionEditorComponent,
    HomeScreenBottomNavigationComponent,
    HomeScreenTranslationsEditorComponent,
    AddTranslationDialogComponent,
    HomeScreenBottomSheetComponent,
    EditListItemTemplateComponent,
    IconSelectorComponent,
    LinkItemTemplateContentEditorComponent,
    HomeScreenTranslationSelectComponent,
  ],
  imports: [
    RouterModule.forChild(routes),
    CommonModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatToolbarModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatSlideToggleModule,
    TranslateModule,
    MatDialogModule,
    NavModule,
    MatCardModule,
    MatProgressBarModule,
    ErrorHandlingModule,
    StoreModule.forFeature(communityFeatureKey, communitiesReducer),
    EffectsModule.forFeature([CommunitiesEffects]),
    MatAutocompleteModule,
    MatChipsModule,
    DragDropModule,
    MatExpansionModule,
  ],
})
export class CommunitiesModule {
}
