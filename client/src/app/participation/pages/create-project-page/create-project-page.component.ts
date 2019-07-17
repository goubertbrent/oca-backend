import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CreateProjectAction } from '../../participation.actions';
import { getProjectDetails, ParticipationState } from '../../participation.state';
import { CreateProject } from '../../projects';

@Component({
  selector: 'oca-create-project-page',
  templateUrl: './create-project-page.component.html',
  styleUrls: [ './create-project-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateProjectPageComponent implements OnInit {
  project: CreateProject = {
    start_date: new Date(),
    description: '',
    action_count: 5000,
    end_date: new Date(),
    budget: {
      amount: 1000,
      currency: 'EUR',
    },
    title: '',
  };
  loading$: Observable<boolean>;

  constructor(private store: Store<ParticipationState>) {
  }

  ngOnInit() {
    this.loading$ = this.store.pipe(select(getProjectDetails), map(p => p.loading));
  }

  createProject(project: CreateProject) {
    this.store.dispatch(new CreateProjectAction(project));
  }
}
