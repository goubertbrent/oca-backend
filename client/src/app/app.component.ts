import { ChangeDetectionStrategy, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'oca-app',
  templateUrl: './app.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {
  constructor(private translate: TranslateService,
              private router: Router,
              private route: ActivatedRoute,
              private store: Store<any>,
              private ngZone: NgZone) {
    window.onmessage = (e: MessageEvent) => {
      if (e.data) {
        ngZone.run(() => {
          switch (e.data.type) {
            case 'oca.set_language':
              translate.use(e.data.language);
              break;
            case 'oca.load_page': // When on a subpage of the desired page, don't do anything to keep state
              if (e.data.paths.length === 1) {
                if (route.snapshot.firstChild && route.snapshot.firstChild.routeConfig
                  && route.snapshot.firstChild.routeConfig.path !== e.data.paths[ 0 ]) {
                  router.navigate(e.data.paths);
                }
              }
              break;
            case 'channel':
              if (e.data.data.type === 'client-action') {
                this.store.dispatch(e.data.data.action);
              }
              break;
          }
        });
      }
    };
    translate.use('nl');
    translate.setDefaultLang('en');
  }
}
