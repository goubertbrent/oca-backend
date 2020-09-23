import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { getSidebarItems } from '../../../../framework/client/nav/sidebar';
import { NavigationItem } from '../../interfaces';

@Component({
  selector: 'rcc-home-page',
  templateUrl: 'home-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})

export class HomePageComponent implements OnInit {
  navigationItems$: Observable<NavigationItem[]>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.navigationItems$ = this.store.pipe(select(getSidebarItems)).pipe(map(items => items.filter(i => i.id !== 'home')));
  }

}
