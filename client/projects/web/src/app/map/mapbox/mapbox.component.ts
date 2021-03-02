/* tslint:disable:no-trailing-whitespace */
import {Component, OnInit} from '@angular/core';
import {select, Store} from '@ngrx/store';
import {clickMarker} from '../map.actions';

import * as  mapboxgl from 'mapbox-gl';
import {Marker, SelectedMarker} from "../marker.model";
import {environment} from "../../../environments/environment";
import {Observable} from "rxjs";
import {getLayerId, getPreviousLayerId} from "../map.selectors";

interface Source {
  sourceId: string;
  tileId: string;
  tileName: string;
}

@Component({
  selector: 'app-mapbox',
  templateUrl: './mapbox.component.html',
  styleUrls: ['./mapbox.component.scss']
})
export class MapboxComponent implements OnInit {
  //private layers = [this.servicesCityLayerId, this.servicesProfitLayerId,this.servicesNonProfitLayerId,this.servicesCareLayerId]
  private layers = [environment.servicesCityLayerId]
  selectedLayerId$: Observable<string>;
  previousLayerId$: Observable<string>;

  private map: any;

  constructor(private store: Store) {}

  public onClickMarker(feature: Marker) {
    let test: SelectedMarker = {
      'id': feature.id,
      'properties': JSON.parse(feature.properties.data),
      'type': feature.type,
      'geometry': feature.geometry,
    }
    this.store.dispatch(clickMarker({selectedMarker: test}));
  }

  ChangeLayer(layerId: string, visibility: string): void {
    if(layerId != "")
    {
      this.map.setLayoutProperty(layerId, 'visibility', visibility);
    }
  }

  ngOnInit(): void {
    this.map = new mapboxgl.Map({
      accessToken: 'pk.eyJ1IjoiZmFpcnZpbGxlIiwiYSI6ImNrbDZkb2ppNzFjeXQycW1uOGM0cDY1NmQifQ.-l4ZEOYtpkk39Re3txcSNw',
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [3.7174, 51.0543],
      maxZoom: 20,
      minZoom: 5,
      zoom: 10
    });

    const servicesCity = {
      sourceId: environment.servicesCityLayerId,
      tileId: 'fairville.services_city',
      tileName: 'services_city'
    };
    const servicesNonProfit = {
      sourceId: environment.servicesNonProfitLayerId, tileId: 'fairville.services_non_profit',
      tileName: 'services_non_profit'
    };
    const servicesProfit = {
      sourceId: environment.servicesProfitLayerId,
      tileId: 'fairville.services_profit',
      tileName: 'services_profit'
    };
    const servicesCare = {
      sourceId: environment.servicesCareLayerId,
      tileId: 'fairville.services_emergency',
      tileName: 'services_emergency'
    };

// Create a popup, but don't add it to the map yet.
    const popup = new mapboxgl.Popup({
      closeButton: false
    });

    this.map.on('load', () => {

      this.map.resize();

      this.addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/manifestation?eventType=betoging&size=64&grey=false', 'manifestIcon');
      this.addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/workassignment?important=false&size=64&grey=false', 'workassignmentOrangeIcon');
      this.addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/workassignment?important=true', 'workassignmentRedIcon');


      this.addSource(servicesCity);
      this.addSource(servicesProfit);
      this.addSource(servicesNonProfit);
      this.addSource(servicesCare);


      this.map.addLayer({
        id: environment.servicesCityLayerId,
        source: servicesCity.sourceId,
        'source-layer': servicesCity.tileName,
        type: 'symbol',
        layout: this.setLayout()
      });

      this.map.addLayer({
        id: environment.servicesProfitLayerId,
        source: servicesProfit.sourceId,
        'source-layer': servicesProfit.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'none'
        }
      });

      this.map.addLayer({
        id: environment.servicesNonProfitLayerId,
        source: servicesNonProfit.sourceId,
        'source-layer': servicesNonProfit.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'none'
        }
      });

      this.map.addLayer({
        id: environment.servicesCareLayerId,
        source: servicesCare.sourceId,
        'source-layer': servicesCare.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'none'
        }
      });

      this.selectedLayerId$ = this.store.pipe(select(getLayerId));
      this.previousLayerId$ = this.store.pipe(select(getPreviousLayerId));
      this.selectedLayerId$.subscribe(
        id => {
          this.ChangeLayer(id, 'visible');
          console.log(id)
        }
      );
      this.previousLayerId$.subscribe(
        id => {
          this.ChangeLayer(id, 'none');
          console.log(id)
        }
      );


      this.map.on('moveend', () => {
        // @ts-ignore
        const features: Marker[] = this.map.queryRenderedFeatures({layers: this.layers});
      });

      this.map.on('mousemove', environment.servicesProfitLayerId, (e: any) => {
// Change the cursor style as a UI indicator.
        this.map.getCanvas().style.cursor = 'pointer';

// Populate the popup and set its coordinates based on the feature.
        if (!e.features) {
          return;
        }
        const feature = e.features[0];
        const geometry = feature.geometry as any;
        popup
          .setLngLat(geometry.coordinates)
          .setText(feature.properties!.description)
          .addTo(this.map);
      });


      this.map.on('mouseleave', environment.servicesProfitLayerId, () => {
        this.map.getCanvas().style.cursor = '';
        popup.remove();
      });

      this.map.on('click', environment.servicesCityLayerId, (e: any) => {
// Change the cursor style as a UI indicator.
        this.map.getCanvas().style.cursor = 'pointer';

// Populate the popup and set its coordinates based on the feature.
        if (!e.features) {
          return;
        }
        const feature: Marker = e.features[0];
        popup
          .setLngLat([feature.geometry.coordinates[0], feature.geometry.coordinates[1]])
          .setText(
            feature.properties.id
          )
          .addTo(this.map);
        this.onClickMarker(feature);
      });
    });
  }

  addImage(url: string, name: string): void {
    this.map.loadImage(
      url,
      (error: any, image: any) => {
        if (error) {
          throw error;
        }
        this.map.addImage(name, image as any);
      });
  }

  addSource(source: Source) {
    const url = 'mapbox://' + source.tileId;
    this.map.addSource(source.sourceId, {
      type: 'vector',
      url
    });
  }

  private setLayout() {
    return {
      'icon-image': 'manifestIcon',
      'icon-size': 0.35,
      'icon-allow-overlap': true,
      'visibility': 'visible'
    };
  }
}


