import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { markFormGroupTouched } from '@oca/shared';
import { Observable } from 'rxjs';
import { LoginAction } from '../../hoplr.actions';
import { HoplrAppState, isLoggingIn } from '../../state';

@Component({
  selector: 'hoplr-signin-page',
  templateUrl: './signin-page.component.html',
  styleUrls: ['./signin-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SigninPageComponent implements OnInit {
  signinForm = new FormGroup({
    username: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required]),
  });
  loading$: Observable<boolean>;

  constructor(private store: Store<HoplrAppState>) {
  }

  ngOnInit() {
    this.loading$ = this.store.pipe(select(isLoggingIn));
  }

  signIn() {
    if (this.signinForm.valid) {
      const { username, password } = this.signinForm.value;
      this.store.dispatch(new LoginAction({ username, password }));
    } else {
      markFormGroupTouched(this.signinForm);
    }
  }

}
