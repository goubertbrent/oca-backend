import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { getCirkloInfo } from '../../cirklo.selectors';

type Tab = { label: string; route: string; iconName: string | null; iconSrc: string | null };

@Component({
  selector: 'cirklo-home',
  templateUrl: './cirklo-home.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CirkloHomePage {
  tabs$: Observable<Tab[]>;

  constructor(private store: Store) {
    this.tabs$ = this.store.pipe(select(getCirkloInfo), map(info => {
      const tabs = [
        { label: 'app.cirklo.vouchers', route: 'vouchers', iconName: null, iconSrc: '/assets/icon/business-and-finance.svg' },
        { label: 'app.cirklo.merchants', route: 'merchants', iconName: 'cart', iconSrc: null },
      ];
      if (info) {
        tabs.push({
          label: 'app.cirklo.buy_voucher',
          route: 'info',
          iconName: null,
          iconSrc: '/assets/icon/cirklo_light_white_filled.svg',
        });
      }
      return tabs;
    }));
  }
}
