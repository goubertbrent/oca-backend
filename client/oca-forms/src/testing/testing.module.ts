import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';

class TranslateServiceStub implements TranslateLoader {

  getTranslation(lang: string): Observable<any> {
    return of({});
  }
}


@NgModule({
  imports: [
    BrowserAnimationsModule,
    FormsModule,
    StoreModule.forRoot({}, {
      runtimeChecks: {
        strictActionImmutability: false,
        strictActionSerializability: true,
        strictStateImmutability: false,
        strictStateSerializability: true,
      },
    }),
    EffectsModule.forRoot([]),
    TranslateModule.forRoot({
      loader: { provide: TranslateLoader, useClass: TranslateServiceStub },
    }),
  ],
  exports: [],
  declarations: [],
  providers: [],
})
export class TestingModule {
}
