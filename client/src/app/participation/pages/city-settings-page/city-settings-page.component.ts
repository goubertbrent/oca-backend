import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { deepCopy } from '../../../shared/util';
import { GetSettingsAction, UpdateSettingsAction } from '../../participation.actions';
import { getSettings, ParticipationState } from '../../participation.state';
import { CitySettings } from '../../projects';

@Component({
  selector: 'oca-city-settings-page',
  templateUrl: './city-settings-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CitySettingsPageComponent implements OnInit {

  citySettings$: Observable<Loadable<CitySettings>>;

  constructor(private store: Store<ParticipationState>) {
  }

  ngOnInit() {
    this.citySettings$ = this.store.pipe(select(getSettings), map(s => deepCopy(s)));
    this.store.dispatch(new GetSettingsAction());
  }

  updateSettings(settings: CitySettings) {
    this.store.dispatch(new UpdateSettingsAction(settings));
  }

}
