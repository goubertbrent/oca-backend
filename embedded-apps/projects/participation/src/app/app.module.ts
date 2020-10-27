import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  PreloadAllModules,
  RouteReuseStrategy,
  RouterModule,
  RouterStateSnapshot,
  Routes,
  UrlTree,
} from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';

import { IonicModule, IonicRouteStrategy, Platform } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { RogerthatEffects, rogerthatReducer } from '@oca/rogerthat';
import { CUSTOM_LOCALE_PROVIDER, HttpLoaderFactory, MissingTranslationWarnHandler } from '@oca/shared';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';

@Injectable()
class CanActivateRoute implements CanActivate {

  constructor(private platform: Platform) {
  }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean | UrlTree> |
    Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.platform.ready().then(() => true);
  }

}

const routes: Routes = [
  {
    canActivate: [CanActivateRoute],
    path: '',
    loadChildren: () => import('./projects/projects.module').then(m => m.ProjectsModule),
  },
];


@NgModule({
  declarations: [AppComponent],
  entryComponents: [],
  imports: [
    BrowserModule,
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules }),
    HttpClientModule,
    IonicModule.forRoot(environment.production ? undefined : { mode: Math.random() > .5 ? 'ios' : 'md' }),
    StoreModule.forRoot({ rogerthat: rogerthatReducer } as any),
    EffectsModule.forRoot([RogerthatEffects]),
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient],
      },
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
    environment.extraImports,
  ],
  providers: [
    CanActivateRoute,
    StatusBar,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    CUSTOM_LOCALE_PROVIDER,
  ],
  bootstrap: [AppComponent],
})
export class AppModule {

}
