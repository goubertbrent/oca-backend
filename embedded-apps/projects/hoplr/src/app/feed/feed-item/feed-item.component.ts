import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { HoplrFeedItem, HoplrRate } from '../../hoplr';

@Component({
  selector: 'hoplr-feed-item',
  templateUrl: './feed-item.component.html',
  styleUrls: ['./feed-item.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedItemComponent implements OnChanges {
  @Input() item: HoplrFeedItem;
  @Input() baseUrl: string;

  rates: HoplrRate[] = [];
  commentRatesMap = new Map<number, HoplrRate[]>();

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.item) {
      this.setRates();
    }
  }

  private setRates() {
    const normalRates: HoplrRate[] = [];
    this.commentRatesMap.clear();
    this.rates = this.item.data.Rates.filter(rate => rate.CommentId === null);
    for (const rate of this.item.data.Rates) {
      if (rate.CommentId === null) {
        normalRates.push(rate);
      } else {
        const commentRates = this.commentRatesMap.get(rate.CommentId) ?? [];
        commentRates.push(rate);
        this.commentRatesMap.set(rate.CommentId, commentRates);
      }
    }
    this.rates = normalRates;
  }
}
