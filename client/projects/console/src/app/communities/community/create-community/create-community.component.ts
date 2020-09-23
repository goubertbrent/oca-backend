import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ListEmbeddedAppsAction } from '../../../actions';
import { getEmbeddedApps } from '../../../console.state';
import { EmbeddedApp } from '../../../interfaces';
import { Community, CreateCommunity, SimpleApp } from '../communities';
import { isCommunityLoading } from '../../communities.selectors';
import { createCommunity } from '../../community.actions';
import { CommunityService } from '../../community.service';

@Component({
  selector: 'rcc-create-community',
  templateUrl: './create-community.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateCommunityComponent implements OnInit {
  apps$: Observable<SimpleApp[]>;
  embeddedApps$: Observable<EmbeddedApp[]>;
  community$: Observable<Community>;
  communityLoading$: Observable<boolean>;

  constructor(private store: Store,
              private communityService: CommunityService) {
  }

  ngOnInit(): void {
    this.store.dispatch(new ListEmbeddedAppsAction());
    this.embeddedApps$ = this.store.pipe(select(getEmbeddedApps));
    this.communityLoading$ = this.store.pipe(select(isCommunityLoading));
    this.apps$ = this.communityService.getApps();
  }

  createCommunity(community: CreateCommunity) {
    this.store.dispatch(createCommunity({ community }));
  }

}
