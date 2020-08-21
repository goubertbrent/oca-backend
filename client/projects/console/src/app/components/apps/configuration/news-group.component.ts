import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { UpdateNewsGroupImageAction } from '../../../actions';
import { App, UpdateNewsImagePayload } from '../../../interfaces';
import { FileSelector } from '../../../util';

@Component({
  selector: 'rcc-news-group',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
  <rcc-news-group-from (save)="submit($event)"></rcc-news-group-from>`,
})
export class NewsGroupComponent extends FileSelector implements OnInit {
  app$: Observable<App>;
  appId: string;
  groupId: string;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute) {
    super();
  }

  ngOnInit() {
    this.appId = (<ActivatedRouteSnapshot>(<ActivatedRouteSnapshot>this.route.snapshot.parent).parent).params.appId;
    this.groupId = this.route.snapshot.params.groupId;
  }

  submit(payload: UpdateNewsImagePayload) {
    this.store.dispatch(new UpdateNewsGroupImageAction(this.groupId, payload));
  }
}
