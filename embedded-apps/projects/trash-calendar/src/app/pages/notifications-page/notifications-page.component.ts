import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { withLatestFrom } from 'rxjs/operators';
import { getNotifications, getNotificationTypes, isSavingNotifications, TrashAppState } from '../../state';
import { TrashActivity } from '../../trash';
import { SaveNotifications } from '../../trash.actions';

@Component({
  selector: 'trash-notifications-page',
  templateUrl: './notifications-page.component.html',
  styleUrls: ['./notifications-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificationsPageComponent implements OnInit {
  formGroup = new FormGroup({});

  notifications$: Observable<string[]>;
  notificationsTypes$: Observable<TrashActivity[]>;
  isSavingNotifications$: Observable<boolean>;
  enabledNotifications: { [ key: string ]: boolean } = {};

  constructor(private store: Store<TrashAppState>) {
  }

  ngOnInit() {
    this.notifications$ = this.store.pipe(select(getNotifications));
    this.notificationsTypes$ = this.store.pipe(select(getNotificationTypes));
    this.isSavingNotifications$ = this.store.pipe(select(isSavingNotifications));
    this.notificationsTypes$.pipe(withLatestFrom(this.notifications$)).subscribe(([types, enabledNotifications]) => {
      for (const type of types) {
        this.formGroup.removeControl(type.key);
        this.formGroup.addControl(type.key, new FormControl(enabledNotifications.includes(type.key)));
      }
    });
  }

  saveNotifications() {
    const notifications: string[] = Object.keys(this.formGroup.value).filter(key => this.formGroup.value[ key ] === true);
    this.store.dispatch(new SaveNotifications({ notifications }));
  }
}
