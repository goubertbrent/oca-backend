import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { SecondarySidebarItem, SidebarTitle } from '../../../../framework/client/nav/sidebar';
import { filterNull } from '../../ngrx';
import { ClearDeveloperAccountAction, GetDeveloperAccountAction } from '../../actions';
import { getDeveloperAccount } from '../../console.state';

@Component({
  selector: 'rcc-developer-account-details',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<secondary-sidenav [sidebarItems]="sidebarItems" [sidebarTitle]="title$ | async"></secondary-sidenav>',
})
export class DeveloperAccountDetailsComponent implements OnInit {
  sidebarItems: SecondarySidebarItem[] = [
    {
      label: 'rcc.details',
      icon: 'dashboard',
      route: 'details',
    }
  ];
  title$: Observable<SidebarTitle>;
  constructor(private store: Store, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.store.dispatch(new ClearDeveloperAccountAction());
    this.store.dispatch(new GetDeveloperAccountAction(this.route.snapshot.params.accountId));
    this.title$ = this.store.pipe(select(getDeveloperAccount), filterNull(), map(d => ({
      isTranslation: false,
      label: d.name,
    })));
  }
}
