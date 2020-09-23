import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { NavigationItem } from '../../../interfaces/misc.interfaces';

@Component({
  selector: 'rcc-app-assets',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<rcc-navigation-cards [navigationItems]="navigationItems"></rcc-navigation-cards>',
})
export class AppAssetsOverviewComponent implements OnInit {
  navigationItems: NavigationItem[];

  public ngOnInit(): void {
    this.navigationItems = [ {
      label: 'rcc.core_branding',
      description: 'rcc.core_branding_explanation',
      icon: 'looks',
      route: 'core-branding',
    }, {
      label: 'rcc.qr_templates',
      description: 'rcc.qr_templates_explanation',
      icon: 'qr_code',
      route: 'qr-code-templates',
    }, {
      label: 'rcc.resources',
      description: 'rcc.resources_explanation',
      icon: 'photo',
      route: 'resources',
    }, {
      label: 'rcc.brandings',
      description: 'rcc.brandings_explanation',
      icon: 'insert_photo',
      route: 'brandings',
    } ];
  }
}
