import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { CallStateType, ResultState } from '@oca/shared';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { City } from '../../projects';
import { GetCityAction } from '../../projects.actions';
import { getCity, ProjectsState } from '../../projects.state';

@Component({
  selector: 'pp-projects-page',
  templateUrl: './info-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class InfoPageComponent {
  city$: Observable<ResultState<City>>;
  isLoading$: Observable<boolean>;

  constructor(private store: Store<ProjectsState>) {
    this.store.dispatch(new GetCityAction({ id: rogerthat.system.appId }));
    this.city$ = this.store.pipe(select(getCity));
    this.isLoading$ = this.city$.pipe(map(c => c.state === CallStateType.LOADING));
  }
}
