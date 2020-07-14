// This file can be replaced during build by using the `fileReplacements` array.
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.
import '../../../rogerthat/src/testing/fake-rogerthat';
import { TrashTestEffects } from '../app/trash.test.effects';

export const environment = {
  production: false,
  extraImports: [
    StoreDevtoolsModule.instrument({
      name: 'Trash calendar',
      maxAge: 25, // Retains last 25 states
    })],
  ngrxEffects: [TrashTestEffects],
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.
