import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit {
  selectedfeature: any;
  constructor() { }

  ngOnInit(): void {
  }

  public getFeature(feature: any) {
    this.selectedfeature = feature;
  }

}
