import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable, NonNullLoadable } from '../../../shared/loadable/loadable';
import { GetProjectsAction } from '../../participation.actions';
import { getProjects, ParticipationState } from '../../participation.state';
import { Project } from '../../projects';

interface ProjectsTab {
  label: string;
  projects: NonNullLoadable<Project[]>;
}

@Component({
  selector: 'oca-project-list-page',
  templateUrl: './project-list-page.component.html',
  styleUrls: ['./project-list-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectListPageComponent implements OnInit {
  tabs$: Observable<ProjectsTab[]>;
  projects$: Observable<Loadable<Project[]>>;
  hasNoProjects$: Observable<boolean>;

  constructor(private store: Store<ParticipationState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetProjectsAction());
    this.projects$ = this.store.pipe(select(getProjects));
    this.hasNoProjects$ = this.projects$.pipe(map(p => p.success && p.data && p.data.length === 0 || false));
    this.tabs$ = this.projects$.pipe(map(projects => {
      const now = new Date();
      const activeProjects = [];
      const finishedProjects = [];
      for (const project of projects.data || []) {
        if (new Date(project.end_date) > now) {
          activeProjects.push(project);
        } else {
          finishedProjects.push(project);
        }
      }
      return [
        { label: 'oca.current_projects', projects: { ...projects, data: activeProjects } },
        { label: 'oca.finished_projects', projects: { ...projects, data: finishedProjects } },
      ];
    }));
  }

}
