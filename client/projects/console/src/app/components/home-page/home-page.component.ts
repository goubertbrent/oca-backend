import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { getSidebarItems } from '../../../../framework/client/nav/sidebar/sidebar.state';
import { NavigationItem } from '../../interfaces';

@Component({
  selector: 'rcc-home-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  templateUrl: 'home-page.component.html',
})

export class HomePageComponent implements OnInit {
  navigationItems$: Observable<NavigationItem[]>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.navigationItems$ = this.store.pipe(select(getSidebarItems)).pipe(map(items => items.filter(i => i.id !== 'home')));
  }

}
