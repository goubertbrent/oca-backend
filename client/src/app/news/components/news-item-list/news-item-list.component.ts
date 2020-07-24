import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { NewsItem, ServiceNewsGroup } from '@oca/web-shared';
import { Loadable } from '../../../shared/loadable/loadable';
import { NewsListItem } from '../../news';

@Component({
  selector: 'oca-news-item-list',
  templateUrl: './news-item-list.component.html',
  styleUrls: [ './news-item-list.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemListComponent implements OnChanges {
  @Input() items: NewsListItem[];
  @Input() hasMore: boolean;
  @Input() listStatus: Loadable;
  @Input() newsGroups: ServiceNewsGroup[];
  @Output() deleteItem = new EventEmitter<NewsItem>();
  @Output() copyItem = new EventEmitter<NewsItem>();
  @Output() loadMore = new EventEmitter();

  newsGroupsMapping: { [ key: string ]: string } = {};

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.newsGroups && this.newsGroups) {
      this.newsGroupsMapping = {};
      for (const group of this.newsGroups) {
        this.newsGroupsMapping[ group.group_type ] = group.name;
      }
    }
  }

  trackNews(index: number, item: NewsItem) {
    return item.id;
  }
}
