import { animate, state, style, transition, trigger } from '@angular/animations';
import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { CirkloMerchant } from '../../cirklo';
import { getMerchant } from '../../cirklo.selectors';

@Component({
  selector: 'app-merchant-details-page',
  templateUrl: './merchant-details-page.component.html',
  styleUrls: ['./merchant-details-page.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
    trigger('chevronAnimation', [
      // rotate chevron when expanded
      state('true', style({ transform: 'rotate(-180deg)' })),
      transition(`* <=> *`, [
        animate('250ms cubic-bezier(0.4, 0.0, 0.2, 1)'),
      ]),
    ]),
  ],
})
export class MerchantDetailsPageComponent implements OnInit {
  merchant$: Observable<CirkloMerchant | undefined>;
  openingHoursExpanded = false;

  constructor(private store: Store,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    const merchantId = this.route.snapshot.params.id;
    // Only accessible after having visited the 'merchants' page but that shouldn't be a problem when used in the app
    this.merchant$ = this.store.pipe(select(getMerchant, merchantId));
  }

  toggleOpeningHours() {
    this.openingHoursExpanded = !this.openingHoursExpanded;
  }
}
