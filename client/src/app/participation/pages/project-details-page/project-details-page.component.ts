import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { deepCopy } from '../../../shared/util/misc';
import {
  GetMoreProjectStatisticsAction,
  GetProjectAction,
  GetProjectStatisticsAction,
  SaveProjectAction,
} from '../../participation.actions';
import { getProjectDetails, getProjectStatistics, ParticipationState } from '../../participation.state';
import { Project, ProjectStatistics } from '../../projects';

@Component({
  selector: 'oca-project-details-page',
  templateUrl: './project-details-page.component.html',
  styleUrls: ['./project-details-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectDetailsPageComponent implements OnInit {
  project$: Observable<Loadable<Project>>;
  projectStatistics$: Observable<Loadable<ProjectStatistics>>;
  id: number;

  constructor(private store: Store<ParticipationState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.id = parseInt(this.route.snapshot.params.id, 10);
    this.store.dispatch(new GetProjectAction({ id: this.id }));
    this.project$ = this.store.pipe(select(getProjectDetails), map(s => deepCopy(s)));
    this.projectStatistics$ = this.store.pipe(select(getProjectStatistics));
  }

  save(project: Project) {
    this.store.dispatch(new SaveProjectAction(project));
  }

  onTabChange(event: MatTabChangeEvent) {
    if (event.index === 1) {
      this.store.dispatch(new GetProjectStatisticsAction({ id: this.id }));
    }
  }

  loadMoreStatistics() {
    this.store.dispatch(new GetMoreProjectStatisticsAction());
  }
}
