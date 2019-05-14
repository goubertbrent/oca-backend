import { AgmCoreModule } from '@agm/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { GoogleChartsModule } from 'angular-google-charts';
import { SIMPLEMDE_CONFIG, SimplemdeModule } from 'ng2-simplemde';
import { Options as SimpleMDEOptions } from 'simplemde';
import { environment } from '../../environments/environment';
import { SimpleDialogComponent } from './dialog/simple-dialog.component';
import { LoadableComponent } from './loadable/loadable.component';
import { UserAutoCompleteDialogComponent } from './users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserAutocompleteComponent } from './users/components/user-autocomplete/user-autocomplete.component';


@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    TranslateModule,
    GoogleChartsModule.forRoot(),
    AgmCoreModule.forRoot({
      apiKey: environment.googleMapsKey,
    }),
    SimplemdeModule.forRoot({
      provide: SIMPLEMDE_CONFIG,
      useValue: {
        autoDownloadFontAwesome: false,
        spellChecker: false,
        status: false,
        toolbar: [ 'bold', 'italic', 'strikethrough', 'unordered-list', 'link' ],
      } as SimpleMDEOptions,
    }),
    MatAutocompleteModule,
    MatButtonModule,
    MatCheckboxModule,
    MatSnackBarModule,
    MatChipsModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatProgressSpinnerModule,
    MatFormFieldModule,
  ],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    TranslateModule,
    GoogleChartsModule,
    AgmCoreModule,
    SimplemdeModule,
    SimpleDialogComponent,
    LoadableComponent,
    UserAutoCompleteDialogComponent,
    UserAutocompleteComponent,
  ],
  declarations: [
    SimpleDialogComponent,
    LoadableComponent,
    UserAutoCompleteDialogComponent,
    UserAutocompleteComponent,
  ],
  providers: [],
  entryComponents: [
    SimpleDialogComponent,
    LoadableComponent,
    UserAutoCompleteDialogComponent,
    UserAutocompleteComponent,
  ],
})
export class SharedModule {
  constructor(private translate: TranslateService, private router: Router) {
    window.onmessage = e => {
      if (e.data && e.data.type === 'oca.set_language') {
        translate.use(e.data.language);
      }
      if (e.data && e.data.type === 'oca.load_page') {
        router.navigate(e.data.paths);
      }
    };
    translate.use('nl');
    translate.setDefaultLang('en');
  }
}
