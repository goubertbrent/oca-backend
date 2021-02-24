import {Component, Input, OnInit} from '@angular/core';
import {Marker} from "../../marker.model";
import {select, Store} from '@ngrx/store';
import {Observable} from "rxjs";
import {getSelectedMarker} from '../../map.selectors'

@Component({
  selector: 'app-marker-detail',
  templateUrl: './marker-detail.component.html',
  styleUrls: ['./marker-detail.component.scss']
})
export class MarkerDetailComponent implements OnInit {
  marker$: Observable<Marker | null>;

  constructor(private store: Store) { }

  ngOnInit(): void {
     this.marker$ = this.store.pipe(select(getSelectedMarker));
  }

}
