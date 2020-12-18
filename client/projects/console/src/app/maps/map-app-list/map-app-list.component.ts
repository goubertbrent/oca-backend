import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { RogerthatApp } from '../../interfaces';

@Component({
  selector: 'rcc-map-app-list',
  templateUrl: './map-app-list.component.html',
  styleUrls: ['./map-app-list.component.scss'],
})
export class MapAppListComponent implements OnInit {
  apps$: Observable<RogerthatApp[]>;

  constructor(private http: HttpClient) {
  }

  ngOnInit(): void {
    this.apps$ = this.http.get<RogerthatApp[]>('/console-api/apps');
  }

}
