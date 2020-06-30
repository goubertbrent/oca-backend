import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import '../../../rogerthat/src/testing/fake-rogerthat';
import { HoplrTestEffects } from '../app/testing/hoplr.test.effects';

export const environment = {
  production: false,
  ngrxEffects: [HoplrTestEffects],
  extraAppImports: [
    StoreDevtoolsModule.instrument({
      name: 'Hoplr embedded app',
      maxAge: 25, // Retains last 25 states
    })],
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.
