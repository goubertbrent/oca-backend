import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatStepperModule } from '@angular/material/stepper';
import { RouterModule, Routes } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { BackButtonModule } from '@oca/shared';
import { RegisterPageComponent } from './register-page/register-page.component';
import { SigninHeaderComponent } from './signin-header/signin-header.component';
import { SigninPageComponent } from './signin-page/signin-page.component';

const routes: Routes = [
  { path: '', component: SigninPageComponent },
  { path: 'register', component: RegisterPageComponent },
];

@NgModule({
  declarations: [RegisterPageComponent, SigninPageComponent, SigninHeaderComponent],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    TranslateModule,
    IonicModule,
    BackButtonModule,
    MatStepperModule,
    ReactiveFormsModule,
  ],
})
export class SigninModule {
}
