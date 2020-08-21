import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { NavigationItem } from '../../../interfaces';

@Component({
  selector: 'rcc-appearance',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'appearance.component.html',
})
export class AppearanceComponent implements OnInit {
  navigationLinks: NavigationItem[];

  ngOnInit() {
    this.navigationLinks = [ {
      label: 'rcc.colors',
      route: 'colors',
    }, {
      label: 'rcc.sidebar',
      route: 'sidebar',
    }, {
      label: 'rcc.images',
      route: 'images',
    } ];
  }
}
