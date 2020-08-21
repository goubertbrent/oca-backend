import { Component } from '@angular/core';
import { SecondarySidebarItem, SidebarTitle } from '../../../../framework/client/nav/sidebar/interfaces';

@Component({
  selector: 'rcc-apps',
  template: `
    <secondary-sidenav [sidebarItems]="sidebarItems" [sidebarTitle]="title"></secondary-sidenav>`,
})
export class AppsComponent {
  sidebarItems: SecondarySidebarItem[] = [ {
    label: 'rcc.overview',
    icon: 'view_list',
    route: 'overview',
  }, {
    label: 'rcc.bulk_update',
    icon: 'create',
    route: 'bulk-update',
  }, {
    label: 'rcc.create_app',
    icon: 'add',
    route: 'create',
  } ];
  title: SidebarTitle = {
    isTranslation: true,
    label: 'rcc.apps',
    icon: 'apps',
  };
}
