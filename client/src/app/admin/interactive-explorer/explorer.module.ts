import { CommonModule, DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';
import { MatIconModule, MatIconRegistry } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { DomSanitizer } from '@angular/platform-browser';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, MissingTranslationHandlerParams, TranslateModule, TranslateService } from '@ngx-translate/core';
import { MonacoEditorModule, NgxMonacoEditorConfig } from 'ngx-monaco-editor';
import { environment } from '../../../environments/environment';
import { RunResultDialogComponent } from './components/result-dialog/result-dialog.component';
import { ScriptPageComponent } from './components/script-page.component';
import { ScriptComponent } from './components/script/script.component';
import { ScriptsPageComponent } from './components/scripts-page/scripts-page.component';
import { ScriptsEffects } from './scripts.effect';
import { scriptsReducer } from './scripts.reducer';
import { ScriptsService } from './scripts.service';
import * as translations from './translations.json';

const monacoConfig: NgxMonacoEditorConfig = {
  baseUrl: environment.production ? '/static/client/assets' : '/assets',
  defaultOptions: {
    scrollBeyondLastLine: false,
    theme: 'vs-dark',
    language: 'python',
  },
};

@Injectable()
export class MissingTranslationWarnHandler implements MissingTranslationHandler {

  handle(params: MissingTranslationHandlerParams) {
    console.log(params);
    const lang = params.translateService.currentLang;
    console.warn(`Missing translation for key '${params.key}' for language '${lang}'`);
    return params.key;
  }
}

const routes: Routes = [
  { path: '', component: ScriptsPageComponent },
  { path: ':scriptId', component: ScriptPageComponent },
];

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature('ie', scriptsReducer),
    EffectsModule.forFeature([ScriptsEffects]),
    MonacoEditorModule.forRoot(monacoConfig),
    TranslateModule.forChild({
      missingTranslationHandler: { provide: MissingTranslationHandler, useClass: MissingTranslationWarnHandler },
      isolate: true,
    }),
    MatButtonModule,
    MatDialogModule,
    MatExpansionModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatTooltipModule,
    MatDialogModule,
    MatProgressBarModule,
  ],
  exports: [],
  declarations: [
    ScriptComponent,
    ScriptPageComponent,
    ScriptsPageComponent,
    RunResultDialogComponent,
  ],
  providers: [
    ScriptsService,
    DatePipe,
    {
      provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
      useValue: {
        appearance: 'standard',
      },
    },
  ],
})
export class ExplorerModule {
  constructor(private sanitizer: DomSanitizer,
              private translate: TranslateService,
              private iconRegistry: MatIconRegistry) {
    const icons = `<svg>
  <defs>
    <svg id="logs" fill="currentColor" fill-rule="evenodd" height="100%" viewBox="0 0 24 24" width="100%"
         xmlns="http://www.w3.org/2000/svg" fit="" preserveAspectRatio="xMidYMid meet" focusable="false">
      <path d="M10 7h12V3H10z" opacity=".8"></path>
      <path d="M6 20h4v-2H6zm-2 0h2V8H4z" opacity=".6"></path>
      <path d="M10 21h12v-4H10z" opacity=".8"></path>
      <path d="M6 13h4v-2H6z" opacity=".6"></path>
      <path d="M10 14h12v-4H10z" opacity=".8"></path>
      <path d="M2 8h6V2H2z"></path>
    </svg>
  </defs>
</svg>`;
    iconRegistry.addSvgIconSetLiteralInNamespace('ie', sanitizer.bypassSecurityTrustHtml(icons));
    this.translate.use('en');
    this.translate.setTranslation('en', { ie: translations.ie }, true);
  }
}
