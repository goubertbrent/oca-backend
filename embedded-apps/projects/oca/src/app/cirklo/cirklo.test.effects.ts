import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { RogerthatActionTypes, ScanQrCodeAction, ScanQrCodeUpdateAction } from '@oca/rogerthat';
import { of } from 'rxjs';
import { delay, switchMap } from 'rxjs/operators';
import { CirkloMerchant } from './cirklo';
import {
  AddVoucherAction,
  AddVoucherSuccessAction,
  CirkloActionTypes,
  DeleteVoucherAction,
  DeleteVoucherSuccessAction,
  GetMerchantsCompleteAction,
  GetVoucherTransactionsAction,
  GetVoucherTransactionsCompleteAction,
  LoadVouchersAction,
  LoadVouchersSuccessAction,
} from './cirklo.actions';


const testLogo = 'https://pbs.twimg.com/profile_images/618047344932577281/42i8HgbM_400x400.jpg';
const testCityid = 'abcd';

function randint(min: number, max: number): number {
  return Math.round(Math.random() * (max - min)) + min;
}

@Injectable()
/**
 * Only to be used for testing purposes (not in the app)
 * Basically simulates server responses
 */
export class CirkloTestEffects {
  afterGet$ = createEffect(() => this.actions$.pipe(
    ofType<LoadVouchersAction>(CirkloActionTypes.GET_VOUCHERS),
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(new LoadVouchersSuccessAction({
      main_city_id: testCityid,
      results: [
        { id: '1', cityId: testCityid, expirationDate: '2020-06-20T09:10:14Z', expired: false, amount: 2.5, originalAmount: 27.5 },
        { id: '2', cityId: testCityid, expirationDate: '2020-07-10T09:10:14Z', expired: false, amount: 25, originalAmount: 25 },
        { id: '3', cityId: testCityid, expirationDate: '2020-05-01T09:10:14Z', expired: true, amount: 1, originalAmount: 25 },
        { id: '4', cityId: testCityid, expirationDate: '2020-07-30T09:10:14Z', expired: false, amount: 0, originalAmount: 25 },
        { id: '5', cityId: testCityid, expirationDate: '2020-05-03T09:10:14Z', expired: true, amount: 10, originalAmount: 25 },
      ],
      cities: {
        [ testCityid ]: {
          logo_url: testLogo,
        },
      },
    }))),
  ));

  afterDelete$ = createEffect(() => this.actions$.pipe(
    ofType<DeleteVoucherAction>(CirkloActionTypes.DELETE_VOUCHER),
    delay(randint(50, 500)),
    switchMap(action => of(new DeleteVoucherSuccessAction(action.payload))),
  ));

  getTransactions$ = createEffect(() => this.actions$.pipe(
    ofType<GetVoucherTransactionsAction>(CirkloActionTypes.GET_VOUCHER_TRANSACTIONS),
    delay(randint(50, 500)),
    switchMap(() => of(new GetVoucherTransactionsCompleteAction({ results: [{ id: '1' }, { id: '2' }] }))),
  ));

  scanQr$ = createEffect(() => this.actions$.pipe(
    ofType<ScanQrCodeAction>(RogerthatActionTypes.SCAN_QR_CODE),
    delay(randint(50, 500)),
    switchMap(() => of(new ScanQrCodeUpdateAction({ content: 'some qr', status: 'resolved' }))),
  ));

  addVoucher$ = createEffect(() => this.actions$.pipe(
    ofType<AddVoucherAction>(CirkloActionTypes.ADD_VOUCHER),
    delay(randint(50, 500)),
    switchMap(() => {
      const value = randint(25, 50);
      let remainingValue = 0;
      // 33% chance to be 0, full value or something in between
      switch (randint(0, 2)) {
        case 0:
          remainingValue = 0;
          break;
        case 1:
          remainingValue = randint(0, value);
          break;
        case 2:
          remainingValue = value;
          break;
      }
      const date = new Date(randint(2019, 2021), randint(1, 12), randint(1, 30));
      return of(new AddVoucherSuccessAction({
        voucher: {
          id: randint(6, 5000).toString(),
          cityId: testCityid,
          expirationDate: date.toISOString(),
          expired: date < new Date(),
          amount: remainingValue,
          originalAmount: value,
        },
        city: {
          city_id: testCityid,
          logo_url: testLogo,
        },
      }));
    }),
  ));

  merchantResults: CirkloMerchant[] = [];
  merchants$ = createEffect(() => this.actions$.pipe(
    ofType(CirkloActionTypes.GET_MERCHANTS),
    delay(randint(50, 500)),
    switchMap(() => {
        const result = {
          id: '0',
          name: 'Onze Stad App',
          address: {
            coordinates: {
              lat: 3,
              lon: 50,
            },
            country: 'BE',
            locality: 'Nazareth',
            postal_code: '9810',
            street: 'Steenweg Deinze',
            street_number: '154',
            name: 'Onze Stad App',
            place_id: 'ChIJfYV3cq8Nw0cR-zjpxY5jDzs',
          },
          opening_hours: {
            open_now: true,
            subtitle: null,
            title: 'Open',
            weekday_text: [{
              day: 'maandag',
              lines: [{ color: null, text: 'Gesloten' }],
            },
              {
                day: 'dinsdag',
                lines: [{ color: null, text: '24u open' }],
              },
              {
                day: 'woensdag',
                lines: [{ color: null, text: '24u open' }],
              },
              {
                day: 'donderdag',
                lines: [{ color: null, text: 'Gesloten' }],
              },
              {
                day: 'vrijdag',
                lines: [{ color: null, text: '08:00 - 17:00' }],
              },
              {
                day: 'zaterdag',
                lines: [
                  { color: null, text: 'Gesloten' },
                ],
              },
              {
                day: 'zondag',
                lines: [
                  { color: null, text: '09:00 - 12:00' },
                  { color: '#e69f12', text: 'Uitzonderlijk open voor moederdag' },
                ],
              }],
          },
          email_addresses: [{ value: 'info@onzestadapp.be', name: null }, { value: 'lucas@onzestadapp.be', name: 'Lucas' }],
          phone_numbers: [{ name: null, value: '0032471684984' }, { name: 'Telenet', value: '015 66 66 66' }],
          websites: [{ name: null, value: 'https://onzestadapp.be' }, { name: 'Google', value: 'https://google.com' }],
        };
        const newMerchants = [];
        const start = this.merchantResults.length;
        const end = start + 20;
        for (let i = start; i < end; i++) {
          newMerchants.push({ ...result, id: i.toString(), name: `${result.name} ${i}` });
        }
        this.merchantResults = [...this.merchantResults, ...newMerchants];
        const more = this.merchantResults.length < 100;
        return of(new GetMerchantsCompleteAction({
          more,
          cursor: more ? 'yes' : null,
          results: newMerchants,
        }));
      },
    )));

  constructor(private actions$: Actions) {
  }
}
