import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { NewsItemType, SimpleDialogComponent, SimpleDialogData, NewsGroupType } from '@oca/web-shared';
import { take } from 'rxjs/operators';
import { filterNull } from '../../../shared/util';
import { CreateNews} from '../../news';
import { SetNewNewsItemAction } from '../../news.actions';
import { getNewsOptions, NewsState } from '../../news.state';

@Component({
  selector: 'oca-create-news-page',
  templateUrl: './create-news-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CreateNewsPageComponent implements OnInit {

  constructor(private store: Store<NewsState>,
              private translate: TranslateService,
              private router: Router,
              private matDialog: MatDialog) {
  }

  ngOnInit() {
    const newsOptions$ = this.store.pipe(
      select(getNewsOptions),
      filterNull(),
      take(1),
    );
    // TODO use root ngrx store instead of localStorage
    const itemFromStorage: Partial<CreateNews> | null = JSON.parse(localStorage.getItem('news.item') || '{}');
    newsOptions$.subscribe(newsOptions => {
      if (newsOptions.groups.length === 0) {
        const config: MatDialogConfig<SimpleDialogData> = {
          data: {
            title: this.translate.instant('oca.Error'),
            message: this.translate.instant('oca.news_service_not_reviewed'),
            ok: this.translate.instant('oca.ok'),
          },
        };
        this.matDialog.open(SimpleDialogComponent, config).afterClosed().subscribe(() => this.router.navigate(['news', 'list']));
        return;
      }
      // Prefer city group type as default
      const groups = newsOptions.groups.concat().sort((first, second) => first.group_type === NewsGroupType.CITY ? -1 : 1);
      let item: CreateNews = {
        community_ids: [newsOptions.community_id],
        scheduled_at: null,
        media: null,
        message: '',
        title: '',
        target_audience: null,
        type: NewsItemType.NORMAL,
        action_button: null,
        qr_code_caption: null,
        id: null,
        group_type: groups[ 0 ].group_type,
        locations: null,
        group_visible_until: null,
      };
      if (itemFromStorage) {
        const hasGroup = newsOptions.groups.some(g => g.group_type === itemFromStorage.group_type);
        if (!hasGroup) {
          delete itemFromStorage.group_type;
        }
        item = { ...item, ...itemFromStorage };
        localStorage.removeItem('news.item');
      }
      this.store.dispatch(new SetNewNewsItemAction(item));
    });
  }

}
