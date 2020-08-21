import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { NavigationItem } from '../../interfaces';

@Component({
  selector: 'rcc-app-overview',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav mat-tab-nav-bar>
      <a mat-tab-link
         *ngFor="let item of navigationLinks"
         [routerLink]="[item.route]"
         routerLinkActive #rla="routerLinkActive"
         [active]="rla.isActive">
        {{ item.label | translate }}
      </a>
    </nav>

    <router-outlet></router-outlet>`,
})
export class AppConfigurationComponent implements OnInit {
  navigationLinks: NavigationItem[];

  ngOnInit() {
    this.navigationLinks = [ {
      label: 'rcc.basic_settings',
      route: 'basic',
    }, {
      label: 'rcc.build_settings',
      route: 'build-settings',
    }, {
      label: 'rcc.app_settings',
      route: 'app-settings',
    }, {
      label: 'rcc.advanced_settings',
      route: 'advanced',
    }, {
      label: 'rcc.news_settings',
      route: 'news',
    } ];
  }

}
