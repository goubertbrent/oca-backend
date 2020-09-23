import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ListEmbeddedAppsAction } from '../../../actions';
import { getEmbeddedApps } from '../../../console.state';
import { EmbeddedApp } from '../../../interfaces';
import { filterNull } from '../../../ngrx';
import { getCommunity, isCommunityLoading } from '../../communities.selectors';
import { updateCommunity } from '../../community.actions';
import { CommunityService } from '../../community.service';
import { Community, CreateCommunity, SimpleApp } from '../communities';


@Component({
  selector: 'rcc-edit-community',
  templateUrl: './edit-community.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class EditCommunityComponent implements OnInit {
  apps$: Observable<SimpleApp[]>;
  embeddedApps$: Observable<EmbeddedApp[]>;
  community$: Observable<Community>;
  communityLoading$: Observable<boolean>;

  constructor(private route: ActivatedRoute,
              private store: Store,
              private communityService: CommunityService) {
  }

  ngOnInit(): void {
    this.store.dispatch(new ListEmbeddedAppsAction());
    this.embeddedApps$ = this.store.pipe(select(getEmbeddedApps));
    this.apps$ = this.communityService.getApps();
    this.community$ = this.store.pipe(select(getCommunity), filterNull());
    this.communityLoading$ = this.store.pipe(select(isCommunityLoading));
  }

  save(community: CreateCommunity) {
    const communityId = parseInt(this.route.snapshot.parent!!.params.communityId, 10);
    this.store.dispatch(updateCommunity({ id: communityId, community }));
  }

}
