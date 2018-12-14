import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'oca-create-news-page',
  templateUrl: './create-news-page.component.html',
  styleUrls: [ './create-news-page.component.scss' ],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateNewsPageComponent implements OnInit {

  constructor() {
  }

  ngOnInit() {
  }

}
