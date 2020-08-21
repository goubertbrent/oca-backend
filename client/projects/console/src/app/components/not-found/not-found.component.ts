import { Location } from '@angular/common';
import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'rcc-not-found',
  templateUrl: 'not-found.component.html',
})
export class NotFoundComponent {
  constructor(public router: Router,
              private location: Location) {
    console.error(`Route not found: ${router.url}`);
  }

  goBack() {
    this.location.back();
  }
}
