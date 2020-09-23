import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { CommunityService } from '../../community.service';
import { NEWS_STREAM_TYPES, NewsSettingsWithGroups } from '../news';

@Component({
  selector: 'rcc-news-settings',
  templateUrl: './news-settings.component.html',
  styleUrls: ['./news-settings.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsSettingsComponent implements OnInit {
  newsSettings$: Observable<NewsSettingsWithGroups>;
  communityId: number;
  formGroup = new FormGroup({
    stream_type: new FormControl(null),
  });
  streamTypes = NEWS_STREAM_TYPES;

  constructor(private route: ActivatedRoute,
              private snackbar: MatSnackBar,
              private communityService: CommunityService) {
  }

  ngOnInit() {
    this.communityId = parseInt(this.route.parent?.snapshot.params.communityId, 10);
    this.newsSettings$ = this.communityService.getNewsSettings(this.communityId).pipe(tap(({ stream_type }) => {
      this.formGroup.setValue({ stream_type });
    }));
  }

  saveStream() {
    this.communityService.updateNewsSettings(this.communityId, this.formGroup.value).subscribe(() => {
      this.snackbar.open('News settings saved', 'ok', {duration: 5000});
    });
  }
}
