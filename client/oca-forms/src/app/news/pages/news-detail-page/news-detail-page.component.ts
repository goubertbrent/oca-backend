import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Store } from '@ngrx/store';
import { GetNewsItemAction } from '../../news.actions';
import { NewsState } from '../../news.state';

@Component({
  selector: 'oca-news-detail-page',
  templateUrl: './news-detail-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsDetailPageComponent implements OnInit {
  tabs = [
    { label: 'oca.details', path: 'edit' },
    { label: 'oca.statistics', path: 'statistics' },
  ];

  constructor(private store: Store<NewsState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    const id = this.route.snapshot.params.id;
    this.store.dispatch(new GetNewsItemAction({ id }));
  }

}
