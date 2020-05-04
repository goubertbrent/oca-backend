import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS, MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatRadioModule } from '@angular/material/radio';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { CovalentTextEditorModule } from '@covalent/text-editor';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { DynamicDateModule } from '../shared/dynamic-date/dynamic-date.module';
import { MarkdownModule } from '../shared/markdown/markdown.module';
import { TruncateModule } from '../shared/truncate/truncate.module';
import { JobChatMessageComponent } from './components/job-chat-message/job-chat-message.component';
import { JobEditorComponent } from './components/job-editor/job-editor.component';
import { PublishJobDialogComponent } from './components/publish-job-dialog/publish-job-dialog.component';
import { UnPublishJobDialogComponent } from './components/un-publish-job-dialog/un-publish-job-dialog.component';
import { JobsEffects } from './jobs.effects';
import { jobsReducer } from './jobs.reducer';
import { CreateJobPageComponent } from './pages/create-job-page/create-job-page.component';
import { EditJobPageComponent } from './pages/edit-job-page/edit-job-page.component';
import { JobDetailsPageComponent } from './pages/job-details-page/job-details-page.component';
import { JobOfferListPageComponent } from './pages/job-offer-list-page/job-offer-list-page.component';
import { JobSolicitationPageComponent } from './pages/job-solicitation-page/job-solicitation-page.component';
import { JobSolicitationsListPageComponent } from './pages/job-solicitations-list-page/job-solicitations-list-page.component';
import { JobsSettingsPageComponent } from './pages/jobs-settings-page/jobs-settings-page.component';


const routes: Routes = [
  { path: '', component: JobOfferListPageComponent },
  { path: 'create', component: CreateJobPageComponent },
  { path: 'settings', component: JobsSettingsPageComponent },
  {
    path: ':jobId', component:
    JobDetailsPageComponent,
    children: [
      { path: '', redirectTo: 'details', pathMatch: 'full' },
      { path: 'details', component: EditJobPageComponent },
      {
        path: 'solicitations', component: JobSolicitationsListPageComponent,
        children: [
          { path: ':solicitationId', component: JobSolicitationPageComponent },
        ],
      },
    ],
  },
];


@NgModule({
  declarations: [
    JobOfferListPageComponent,
    EditJobPageComponent,
    JobSolicitationsListPageComponent,
    JobSolicitationPageComponent,
    JobEditorComponent,
    CreateJobPageComponent,
    PublishJobDialogComponent,
    UnPublishJobDialogComponent,
    JobDetailsPageComponent,
    JobChatMessageComponent,
    JobsSettingsPageComponent,
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature('jobs', jobsReducer),
    EffectsModule.forFeature([JobsEffects]),
    MatProgressBarModule,
    MatFormFieldModule,
    CovalentTextEditorModule,
    TranslateModule,
    FormsModule,
    MatSelectModule,
    MatInputModule,
    ReactiveFormsModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatSlideToggleModule,
    MatButtonModule,
    MatDialogModule,
    MatRadioModule,
    MatCardModule,
    MatListModule,
    MatToolbarModule,
    MatIconModule,
    MatTabsModule,
    MarkdownModule,
    TruncateModule,
    MatBadgeModule,
    DynamicDateModule,
    MatChipsModule,
  ],
  providers: [
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'outline' } },
  ],
})
export class JobsModule {
}
