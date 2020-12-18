import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { AppMerchantList } from '../../projects';
import { GetMerchantsAction, GetMoreMerchantsAction } from '../../projects.actions';
import { getMerchants, ProjectsState } from '../../projects.state';

@Component({
  selector: 'pp-merchant-list-page',
  templateUrl: './merchant-list-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class MerchantListPageComponent implements OnInit {
  merchants$: Observable<AppMerchantList | null>;

  constructor(private store: Store<ProjectsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetMerchantsAction());
    this.merchants$ = this.store.pipe(select(getMerchants));
  }

  loadMore() {
    this.store.dispatch(new GetMoreMerchantsAction());
  }

}
