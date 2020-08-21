import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { NavigationItem } from '../../../interfaces/misc.interfaces';

@Component({
  selector: 'rcc-default-settings-overview',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-navigation-cards [navigationItems]="navigationItems"></rcc-navigation-cards>`,
})
export class BackendDefaultSettingsOverviewComponent implements OnInit {
  navigationItems: NavigationItem[];

  ngOnInit() {
    this.navigationItems = [ {
      label: 'rcc.default_app',
      description: 'rcc.default_app_explanation',
      icon: 'apps',
      route: 'app',
    }, {
      label: 'rcc.resources',
      description: 'rcc.default_resources_explanation',
      icon: 'photo',
      route: 'resources',
    }, {
      label: 'rcc.brandings',
      description: 'rcc.default_brandings_explanation',
      icon: 'looks',
      route: 'brandings',
    } ];
  }

}
