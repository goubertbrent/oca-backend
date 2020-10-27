import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild } from '@angular/core';
import { IonInfiniteScroll } from '@ionic/angular';
import { AppMerchant, AppMerchantList } from '../../projects';

@Component({
  selector: 'pp-merchant-list',
  templateUrl: './merchant-list.component.html',
  styleUrls: ['./merchant-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MerchantListComponent implements OnChanges {
  @ViewChild(IonInfiniteScroll, { static: true }) infiniteScroll: IonInfiniteScroll;
  @Input() merchants: AppMerchantList | null;
  @Output() loadMore = new EventEmitter();

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.merchants) {
      if (this.merchants) {
        this.infiniteScroll.complete();
      }
    }
  }

  trackById = (index: number, item: AppMerchant) => item.id;
}
