import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { ListFirebaseProjectsAction } from '../../../actions';
import { getFirebaseProjects, listFirebaseProjectsStatus } from '../../../console.state';
import { FirebaseProject } from '../../../interfaces/firebase-projects';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'firebase-projects-list-page.component.html',
})
export class FirebaseProjectsListPageComponent implements OnInit {
  firebaseProjects$: Observable<FirebaseProject[]>;
  listStatus$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new ListFirebaseProjectsAction());
    this.firebaseProjects$ = this.store.pipe(select(getFirebaseProjects));
    this.listStatus$ = this.store.pipe(select(listFirebaseProjectsStatus));
  }
}
