import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { AlertController } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { first, map } from 'rxjs/operators';
import { areStreetsLoading, getHouseNumbers, getStreets, isSavingAddress, TrashAppState } from '../../state';
import { GetStreetsResult, HouseNumberRequest, TrashHouseNumber, TrashStreet } from '../../trash';
import { GetHouseNumbers, GetStreets, SaveAddress } from '../../trash.actions';

@Component({
  selector: 'trash-set-address-page',
  templateUrl: './set-address-page.component.html',
  styleUrls: ['./set-address-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SetAddressPageComponent implements OnInit {
  addressGroup = new FormGroup({
    street: new FormControl(null, Validators.required),
    houseNumber: new FormControl(null),
    houseNumberInput: new FormControl(null),
  });
  loading$: Observable<boolean>;
  isSavingAddress$: Observable<boolean>;
  streetsResult$: Observable<GetStreetsResult | null>;
  houseNumbers$: Observable<TrashHouseNumber[]>;

  constructor(private store: Store<TrashAppState>,
              private alert: AlertController,
              private translate: TranslateService,
              private cdRef: ChangeDetectorRef) {
  }

  ngOnInit() {
    this.loading$ = this.store.pipe(select(areStreetsLoading));
    this.isSavingAddress$ = this.store.pipe(select(isSavingAddress));
    this.streetsResult$ = this.store.pipe(select(getStreets));
    this.houseNumbers$ = this.store.pipe(select(getHouseNumbers), map(houses => houses.map(h => ({
      ...h,
      label: h.bus ? `${h.number} - ${h.bus}` : h.number,
    }))));
    this.store.dispatch(new GetStreets());
    this.addressGroup.valueChanges.subscribe(() => {
      // Fix retarded issue with ion-select where the label doesn't show until next change detection cycle
      this.cdRef.markForCheck();
    });
    this.addressGroup.controls.street.valueChanges.subscribe((value: TrashStreet) => {
      this.store.dispatch(new GetHouseNumbers({ streetname: value.name, streetnumber: value.number }));
    });
  }

  saveAddress() {
    this.streetsResult$.pipe(first()).subscribe(streetResult => {
      if (!streetResult) {
        return;
      }
      const { street, houseNumber, houseNumberInput } = this.addressGroup.value;
      let msg: string | null = null;
      let house: HouseNumberRequest;
      if (!street) {
        msg = this.translate.instant('app.trash.please_select_street');
      }
      if (streetResult.street_number_via_input) {
        house = { input: houseNumberInput };
        if (!houseNumberInput && !msg) {
          msg = this.translate.instant('app.trash.please_enter_a_house_number');
        }
      } else {
        house = houseNumber;
        if (!houseNumber && !msg) {
          msg = this.translate.instant('app.trash.please_select_a_house_number');
        }
      }
      if (msg) {
        this.alert.create({
          message: msg,
          buttons: [{ text: this.translate.instant('app.trash.ok') }],
        }).then(alert => alert.present());
      } else {
        this.store.dispatch(new SaveAddress({ info: { street, house } }));
      }
    });
  }
}
