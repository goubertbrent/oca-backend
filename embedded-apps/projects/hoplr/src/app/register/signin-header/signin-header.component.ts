import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'hoplr-signin-header',
  templateUrl: './signin-header.component.html',
  styleUrls: ['./signin-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SigninHeaderComponent {
}
