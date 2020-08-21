import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { NavigationItem } from '../../../interfaces';

@Component({
  selector: 'rcc-store-listing-overview',
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
export class StoreListingConfigurationComponent implements OnInit {
  navigationLinks: NavigationItem[];

  ngOnInit() {
    this.navigationLinks = [ {
      label: 'rcc.general_information',
      route: 'general',
    }, {
      label: 'rcc.translations',
      route: 'translations',
    } ];
  }

}
