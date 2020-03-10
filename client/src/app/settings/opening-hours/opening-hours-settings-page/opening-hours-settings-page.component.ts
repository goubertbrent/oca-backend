import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { debounceTime, map } from 'rxjs/operators';
import { OpeningHours } from '../../../shared/interfaces/oca';
import { deepCopy } from '../../../shared/util';
import { GetOpeningHoursAction, SaveOpeningHoursAction } from '../../settings.actions';
import { getOpeningHours, openingHoursLoading, SettingsState } from '../../settings.state';

@Component({
  selector: 'oca-opening-hours-settings-page',
  templateUrl: './opening-hours-settings-page.component.html',
  styleUrls: ['./opening-hours-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningHoursSettingsPageComponent implements OnInit, OnDestroy {
  openingHours$: Observable<OpeningHours | null>;
  isLoading$: Observable<boolean>;

  private autoSave$ = new Subject<OpeningHours>();

  constructor(private store: Store<SettingsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetOpeningHoursAction());
    this.openingHours$ = this.store.pipe(select(getOpeningHours), map(hours => hours && deepCopy(hours)));
    this.isLoading$ = this.store.pipe(select(openingHoursLoading));
    this.autoSave$.pipe(debounceTime(5000)).subscribe(settings => this.onOpeningHoursSaved(settings));
  }

  ngOnDestroy(): void {
    this.autoSave$.unsubscribe();
  }

  onOpeningHoursSaved($event: OpeningHours) {
    this.store.dispatch(new SaveOpeningHoursAction($event));
  }

  autoSave($event: OpeningHours) {
    this.autoSave$.next($event);
  }
}
