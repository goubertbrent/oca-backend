import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { AbstractControl, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatStepper } from '@angular/material/stepper';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { markFormGroupTouched } from '@oca/shared';
import { Observable, Subject } from 'rxjs';
import { map, take, takeUntil } from 'rxjs/operators';
import { Neighbourhood } from '../../hoplr';
import {
  HoplrActions,
  HoplrActionTypes,
  LookupNeighbourhoodAction,
  LookupNeighbourhoodSuccessAction,
  RegisterAction,
} from '../../hoplr.actions';
import { getLookupNeighbourhoodResult, HoplrAppState, isLookingUpNeighbourhood, isRegistering } from '../../state';

@Component({
  selector: 'hoplr-register-page',
  templateUrl: './register-page.component.html',
  styleUrls: ['./register-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegisterPageComponent implements OnInit, OnDestroy {
  @ViewChild('stepper', { static: true }) stepper: MatStepper;
  addressForm = new FormGroup({
    streetName: new FormControl('', [Validators.required]),
    streetNumber: new FormControl('', [Validators.required]),
    cityName: new FormControl('', [Validators.required]),
  });
  invitationForm = new FormGroup({
    invitationCode: new FormControl(''),
  });
  registerForm = new FormGroup({
    firstName: new FormControl(rogerthat.user.firstName, [Validators.required]),
    lastName: new FormControl(rogerthat.user.lastName, [Validators.required]),
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required, Validators.minLength(8)]),
    tos: new FormControl(false, [Validators.required]),
  });
  canRegister = false;
  isLoadingNeighbourhood$: Observable<boolean>;
  isRegistering$: Observable<boolean>;
  neighbourhood$: Observable<Neighbourhood | null>;
  destroyed$ = new Subject();

  constructor(private store: Store<HoplrAppState>,
              private changeDetector: ChangeDetectorRef,
              private actions: Actions<HoplrActions>) {
  }

  ngOnInit() {
    this.actions.pipe(
      takeUntil(this.destroyed$),
      ofType<LookupNeighbourhoodSuccessAction>(HoplrActionTypes.LOOKUP_NEIGHBOURHOOD_SUCCESS),
    ).subscribe(() => {
      this.canRegister = true;
      this.changeDetector.detectChanges();
      this.stepper.next();
    });
    this.neighbourhood$ = this.store.pipe(select(getLookupNeighbourhoodResult),
      map(n => (n?.result.success ? n.result.neighbourhood : null) ?? null));
    this.isLoadingNeighbourhood$ = this.store.pipe(select(isLookingUpNeighbourhood));
    this.isRegistering$ = this.store.pipe(select(isRegistering));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  nextStepAddress() {
    if (this.addressForm.valid) {
      this.stepper.next();
    } else {
      markFormGroupTouched(this.addressForm);
    }
  }

  hasError(control: AbstractControl, errorCode: string) {
    return control.touched && control.hasError(errorCode);
  }

  nextStepInvitation() {
    if (this.invitationForm.valid) {
      const { streetName, streetNumber, cityName } = this.addressForm.value;
      const { invitationCode } = this.invitationForm.value;
      this.store.dispatch(new LookupNeighbourhoodAction({ cityName, streetName, streetNumber, invitationCode }));
    } else {
      markFormGroupTouched(this.invitationForm);
    }
  }

  register() {
    if (this.registerForm.valid) {
      this.store.pipe(select(getLookupNeighbourhoodResult), take(1)).subscribe(neighbourhoodResult => {
        if (neighbourhoodResult?.result.success) {
          const { streetName, streetNumber, cityName } = this.addressForm.value;
          const { firstName, lastName, email, password } = this.registerForm.value;
          const location = neighbourhoodResult.location;
          this.store.dispatch(new RegisterAction({
            info: {
              Street: streetName,
              StreetNumber: streetNumber,
              CityName: cityName,
              Address: location.fullAddress,
              Firstname: firstName,
              LastName: lastName,
              Username: email,
              Password: password,
              Latitude: location.lat,
              Longitude: location.lon,
              NeighbourhoodId: neighbourhoodResult.result.neighbourhood.Id,
              Code: this.invitationForm.value.invitationCode,
            },
          }));
        }
      });
    } else {
      markFormGroupTouched(this.registerForm);
    }
  }
}
