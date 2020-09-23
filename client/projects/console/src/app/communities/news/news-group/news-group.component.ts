import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { App } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { FileSelector } from '../../../util';
import { CommunityService } from '../../community.service';
import { UpdateNewsImagePayload } from '../news';

@Component({
  selector: 'rcc-news-group',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<rcc-news-group-form (save)="submit($event)"></rcc-news-group-form>',
})
export class NewsGroupComponent extends FileSelector implements OnInit {
  app$: Observable<App>;
  communityId: number;
  groupId: string;

  constructor(private store: Store,
              private router: Router,
              private communityService: CommunityService,
              private route: ActivatedRoute) {
    super();
  }

  ngOnInit() {
    this.communityId = parseInt((this.route.snapshot.parent as ActivatedRouteSnapshot).params.communityId, 10);
    this.groupId = this.route.snapshot.params.groupId;
  }

  submit(payload: UpdateNewsImagePayload) {
    this.communityService.updateNewsGroupImage(this.communityId, this.groupId, payload).subscribe(result => {
      this.router.navigate(['..'], {relativeTo: this.route});
    });
  }
}
