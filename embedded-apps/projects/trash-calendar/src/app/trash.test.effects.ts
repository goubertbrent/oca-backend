import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { NavController } from '@ionic/angular';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService, SetUserDataAction } from '@oca/rogerthat';
import { delay, map, startWith, tap } from 'rxjs/operators';
import { ErrorService } from './error.service';
import { TrashUserData } from './state';
import {
  GetHouseNumbersSuccess,
  GetStreets,
  GetStreetsSuccess,
  SaveAddress,
  SaveAddressSuccess,
  SaveNotifications, SaveNotificationsSuccess,
  TrashActionTypes,
} from './trash.actions';
import { TrashEffects } from './trash.effects';

// @formatter:off
const userData: TrashUserData = {
  trash: {notifications: ['christmas_tree', 'plastic_metal_cartons', 'paper_cardboard', 'rest', 'pruning_waste'], notification_types: [{name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, {name: 'Kerstboom', key: 'christmas_tree', icon: 'kerstboom'}, {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, {name: 'Snoeiafval', key: 'pruning_waste', icon: 'tuin'}], collections: [{activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1578009600, year: 2020, day: 3, month: 1}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1578009600, year: 2020, day: 3, month: 1}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1578441600, year: 2020, day: 8, month: 1}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1579046400, year: 2020, day: 15, month: 1}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1579046400, year: 2020, day: 15, month: 1}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1579564800, year: 2020, day: 21, month: 1}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1579651200, year: 2020, day: 22, month: 1}, {activity: {name: 'Kerstboom', key: 'christmas_tree', icon: 'kerstboom'}, epoch: 1579651200, year: 2020, day: 22, month: 1}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1580256000, year: 2020, day: 29, month: 1}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1580256000, year: 2020, day: 29, month: 1}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1580860800, year: 2020, day: 5, month: 2}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1581465600, year: 2020, day: 12, month: 2}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1581465600, year: 2020, day: 12, month: 2}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1581984000, year: 2020, day: 18, month: 2}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1582070400, year: 2020, day: 19, month: 2}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1582675200, year: 2020, day: 26, month: 2}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1582675200, year: 2020, day: 26, month: 2}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1583280000, year: 2020, day: 4, month: 3}, {activity: {name: 'Snoeiafval', key: 'pruning_waste', icon: 'tuin'}, epoch: 1583884800, year: 2020, day: 11, month: 3}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1583884800, year: 2020, day: 11, month: 3}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1583884800, year: 2020, day: 11, month: 3}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1584403200, year: 2020, day: 17, month: 3}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1584489600, year: 2020, day: 18, month: 3}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1585094400, year: 2020, day: 25, month: 3}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1585094400, year: 2020, day: 25, month: 3}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1585699200, year: 2020, day: 1, month: 4}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1586304000, year: 2020, day: 8, month: 4}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1586304000, year: 2020, day: 8, month: 4}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1586822400, year: 2020, day: 14, month: 4}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1586908800, year: 2020, day: 15, month: 4}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1587513600, year: 2020, day: 22, month: 4}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1587513600, year: 2020, day: 22, month: 4}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1588118400, year: 2020, day: 29, month: 4}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1588723200, year: 2020, day: 6, month: 5}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1588723200, year: 2020, day: 6, month: 5}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1589241600, year: 2020, day: 12, month: 5}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1589328000, year: 2020, day: 13, month: 5}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1589932800, year: 2020, day: 20, month: 5}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1589932800, year: 2020, day: 20, month: 5}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1590537600, year: 2020, day: 27, month: 5}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1591142400, year: 2020, day: 3, month: 6}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1591142400, year: 2020, day: 3, month: 6}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1591660800, year: 2020, day: 9, month: 6}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1591747200, year: 2020, day: 10, month: 6}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1592352000, year: 2020, day: 17, month: 6}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1592352000, year: 2020, day: 17, month: 6}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1592956800, year: 2020, day: 24, month: 6}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1593561600, year: 2020, day: 1, month: 7}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1593561600, year: 2020, day: 1, month: 7}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1594080000, year: 2020, day: 7, month: 7}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1594166400, year: 2020, day: 8, month: 7}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1594771200, year: 2020, day: 15, month: 7}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1594771200, year: 2020, day: 15, month: 7}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1595376000, year: 2020, day: 22, month: 7}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1595980800, year: 2020, day: 29, month: 7}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1595980800, year: 2020, day: 29, month: 7}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1596499200, year: 2020, day: 4, month: 8}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1596585600, year: 2020, day: 5, month: 8}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1597190400, year: 2020, day: 12, month: 8}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1597190400, year: 2020, day: 12, month: 8}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1597795200, year: 2020, day: 19, month: 8}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1598400000, year: 2020, day: 26, month: 8}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1598400000, year: 2020, day: 26, month: 8}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1598918400, year: 2020, day: 1, month: 9}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1599004800, year: 2020, day: 2, month: 9}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1599609600, year: 2020, day: 9, month: 9}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1599609600, year: 2020, day: 9, month: 9}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1600214400, year: 2020, day: 16, month: 9}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1600819200, year: 2020, day: 23, month: 9}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1600819200, year: 2020, day: 23, month: 9}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1601337600, year: 2020, day: 29, month: 9}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1601424000, year: 2020, day: 30, month: 9}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1602028800, year: 2020, day: 7, month: 10}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1602028800, year: 2020, day: 7, month: 10}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1602633600, year: 2020, day: 14, month: 10}, {activity: {name: 'Snoeiafval', key: 'pruning_waste', icon: 'tuin'}, epoch: 1603238400, year: 2020, day: 21, month: 10}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1603238400, year: 2020, day: 21, month: 10}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1603238400, year: 2020, day: 21, month: 10}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1603756800, year: 2020, day: 27, month: 10}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1603843200, year: 2020, day: 28, month: 10}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1604448000, year: 2020, day: 4, month: 11}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1604448000, year: 2020, day: 4, month: 11}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1605225600, year: 2020, day: 13, month: 11}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1605657600, year: 2020, day: 18, month: 11}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1605657600, year: 2020, day: 18, month: 11}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1606176000, year: 2020, day: 24, month: 11}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1606262400, year: 2020, day: 25, month: 11}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1606867200, year: 2020, day: 2, month: 12}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1606867200, year: 2020, day: 2, month: 12}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1607472000, year: 2020, day: 9, month: 12}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1608076800, year: 2020, day: 16, month: 12}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1608076800, year: 2020, day: 16, month: 12}, {activity: {name: 'Papier-Karton', key: 'paper_cardboard', icon: 'papier'}, epoch: 1608595200, year: 2020, day: 22, month: 12}, {activity: {name: 'GFT', key: 'vegetable_fruit_garden_waste', icon: 'gft'}, epoch: 1608681600, year: 2020, day: 23, month: 12}, {activity: {name: 'PMD', key: 'plastic_metal_cartons', icon: 'pmd'}, epoch: 1609286400, year: 2020, day: 30, month: 12}, {activity: {name: 'Restafval', key: 'rest', icon: 'huisvuil'}, epoch: 1609286400, year: 2020, day: 30, month: 12}], address: 'Steenweg Deinze 154'}
};
// @formatter:on

@Injectable()
export class TrashTestEffects extends TrashEffects {
  getStreets$ = createEffect(() => this.actions$.pipe(
    ofType<GetStreets>(TrashActionTypes.GetStreets),
    map(action => new GetStreetsSuccess({
      street_number_via_input: false,
      items: [
        { number: 5655612935372800, name: '2de Genielaan' },
        { number: 5092662981951488, name: 'A. Dondeynestraat' },
        { number: 6218562888794112, name: 'Alfons Van Heelaan' },
        { number: 4811188005240832, name: 'Ashoop' },
        { number: 5937087912083456, name: 'Blauwvoet' },
        { number: 5374137958662144, name: 'Boshoek' },
        { number: 6500037865504768, name: 'Brabanthoek' },
        { number: 4670450516885504, name: 'Breydelstraat' },
        { number: 5796350423728128, name: 'Broekstraat' },
        { number: 5233400470306816, name: 'Bulskampstraat' },
        { number: 6359300377149440, name: 'Burgemeester Pietersstraat' },
        { number: 4951925493596160, name: 'Burgweg' },
        { number: 6077825400438784, name: 'Clamarastraat' },
        { number: 5514875447017472, name: 'Collaertshillestraat' },
        { number: 6640775353860096, name: 'Doelweg' },
        { number: 4600081772707840, name: 'Dorpplaats' }],
    })),
  ));

  getHouseNumbers$ = createEffect(() => this.actions$.pipe(
    ofType<GetStreets>(TrashActionTypes.GetHouseNumbers),
    map(action => new GetHouseNumbersSuccess([
        { number: 1, bus: '' },
        { number: 2, bus: '' },
        { number: 3, bus: '' },
        { number: 4, bus: '' },
        { number: 5, bus: '' },
        { number: 6, bus: '' },
        { number: 7, bus: '' },
        { number: 8, bus: '' },
      ]),
    )));
  saveAddress$ = createEffect(() => this.actions$.pipe(
    ofType<SaveAddress>(TrashActionTypes.SaveAddress),
    delay(500),
    map(action => new SaveAddressSuccess()),
    tap(action => {
        this.store.dispatch(new SetUserDataAction(userData));
      },
    )));

  saveNotifications$ = createEffect(() => this.actions$.pipe(
    ofType<SaveNotifications>(TrashActionTypes.SaveNotifications),
    delay(500),
    tap(action => {
      rogerthat.user.data = { trash: { ...rogerthat.user.data.trash, notifications: action.payload.notifications } };
      this.store.dispatch(new SetUserDataAction(rogerthat.user.data));
    }),
    map(action => new SaveNotificationsSuccess()),
  ));

  constructor(protected actions$: Actions,
              protected navController: NavController,
              protected errorService: ErrorService,
              protected store: Store,
              protected rogerthatService: RogerthatService) {
    super(actions$, navController, errorService, store, rogerthatService);
    rogerthat.user.data = userData;
    setTimeout(() => this.store.dispatch(new SetUserDataAction(userData)), 100);
  }
}
