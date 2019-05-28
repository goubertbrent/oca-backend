import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { GetProjectsAction } from '../../participation.actions';
import { getProjects, ParticipationState } from '../../participation.state';
import { Project } from '../../projects';

@Component({
  selector: 'oca-project-list-page',
  templateUrl: './project-list-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class ProjectListPageComponent implements OnInit {
  projects$: Observable<Loadable<Project[]>>;
  hasNoProjects$: Observable<boolean>;

  constructor(private store: Store<ParticipationState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetProjectsAction());
    this.projects$ = this.store.pipe(select(getProjects));
    this.hasNoProjects$ = this.projects$.pipe(map(p => p.success && p.data && p.data.length === 0 || false));
  }

}
