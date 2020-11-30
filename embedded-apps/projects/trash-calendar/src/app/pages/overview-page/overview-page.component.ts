import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { canSetNotifications, getCollections, getCurrentAddress, getLogoUrl, TrashAppState } from '../../state';
import { UITrashCollection } from '../../trash';

@Component({
  selector: 'trash-overview-page',
  templateUrl: './overview-page.component.html',
  styleUrls: ['./overview-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OverviewPageComponent implements OnInit {
  collections$: Observable<UITrashCollection[]>;
  currentAddress$: Observable<string | undefined>;
  logoUrl$: Observable<string | undefined>;
  canSetNotifications$: Observable<boolean>;
  title = rogerthat.menuItem?.label;

  constructor(private store: Store<TrashAppState>) {
  }

  ngOnInit() {
    this.collections$ = this.store.pipe(select(getCollections));
    this.currentAddress$ = this.store.pipe(select(getCurrentAddress));
    this.canSetNotifications$ = this.store.pipe(select(canSetNotifications));
    this.logoUrl$ = this.store.pipe(select(getLogoUrl));
  }

}
