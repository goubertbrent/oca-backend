import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
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
import { NewsGroupFormComponent } from './news/news-group-form/news-group-form.component';
import { NewsGroupComponent } from './news/news-group/news-group.component';
import { NewsSettingsComponent } from './news/news-setings/news-settings.component';

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
  ],
})
export class CommunitiesModule {
}
