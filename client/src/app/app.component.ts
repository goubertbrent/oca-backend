import { ChangeDetectionStrategy, Component, NgZone, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { MainHttpInterceptor } from './shared/main-http-interceptor';

@Component({
  selector: 'oca-app',
  templateUrl: './app.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnInit, OnDestroy {
  private readonly listener: (e: MessageEvent) => void;

  constructor(private translate: TranslateService,
              private router: Router,
              private route: ActivatedRoute,
              private store: Store<any>,
              private ngZone: NgZone) {
    translate.use('nl');
    translate.setDefaultLang('en');
    this.listener = this.channelListener.bind(this);
  }

  ngOnInit(): void {
    window.addEventListener('message', this.listener);
  }

  ngOnDestroy(): void {
    window.removeEventListener('message', this.listener);
  }

  private channelListener(e: MessageEvent) {
    if (e.data) {
      this.ngZone.run(() => {
        switch (e.data.type) {
          case 'oca.init':
            this.translate.use(e.data.language);
            MainHttpInterceptor.serviceEmail = e.data.serviceEmail;
            break;
          case 'oca.load_page':
            const currentUrl = `/${this.route.snapshot.firstChild?.routeConfig?.path}`;
            const newUrl = `/${e.data.paths.join('/')}`;
            if (currentUrl !== newUrl) {
              this.router.navigateByUrl(newUrl);
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
  }
}
