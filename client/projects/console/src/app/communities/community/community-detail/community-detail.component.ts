import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { SecondarySidebarItem, SidebarTitle } from '../../../../../framework/client/nav/sidebar';
import { getCommunity } from '../../communities.selectors';
import { loadCommunity } from '../../community.actions';

@Component({
  templateUrl: './community-detail.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommunityDetailComponent implements OnInit {
  sidebarItems: SecondarySidebarItem[] = [{
    label: 'rcc.settings',
    icon: 'settings',
    route: 'settings',
  }, {
    label: 'rcc.news_settings',
    icon: 'comment',
    route: 'news',
  }];
  title$: Observable<SidebarTitle>;

  constructor(private store: Store,
              private route: ActivatedRoute) {
  }

  ngOnInit(): void {
    const id = parseInt(this.route.snapshot.params.communityId, 10);
    this.store.dispatch(loadCommunity({ id }));
    this.title$ = this.store.pipe(
      select(getCommunity),
      map(community => {
        if (community) {
          return { isTranslation: false, label: community.name };
        } else {
          return { isTranslation: false, label: 'Loading...' };
        }
      }));
  }

}

