/* tslint:disable:no-trailing-whitespace */
import {Component, OnInit, EventEmitter, Output} from '@angular/core';
import {Store} from '@ngrx/store';
import {clickMarker} from '../map.actions';

import * as  mapboxgl from 'mapbox-gl';
import {Marker} from "../marker.model";

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

  private servicesCityLayerId = 'servicesCity';
  private servicesProfitLayerId = 'servicesProfit';
  private servicesNonProfitLayerId = 'servicesNonProfit';
  private servicesCareLayerId = 'servicesCare';
  private layers = [this.servicesCityLayerId, this.servicesProfitLayerId,this.servicesNonProfitLayerId,this.servicesCareLayerId]

  constructor(private store: Store) {
  }

  public onClickMarker(feature: Marker) {
    let test: Marker = {
      'id': feature.id,
      'properties': feature.properties,
      'type': feature.type,
      'geometry': feature.geometry,
    }
    this.store.dispatch(clickMarker({selectedMarker: test})); // moet object zijn
  }

  ngOnInit(): void {

    const servicesCity = {sourceId: this.servicesCityLayerId, tileId: 'fairville.services_city', tileName: 'services_city'};
    const servicesNonProfit = {
      sourceId: this.servicesNonProfitLayerId, tileId: 'fairville.services_non_profit',
      tileName: 'services_non_profit'
    };
    const servicesProfit = {
      sourceId: this.servicesProfitLayerId,
      tileId: 'fairville.services_profit',
      tileName: 'services_profit'
    };
    const servicesCare = {
      sourceId: this.servicesCareLayerId,
      tileId: 'fairville.services_emergency',
      tileName: 'services_emergency'
    };


    const map = new mapboxgl.Map({
      accessToken: 'pk.eyJ1IjoiZmFpcnZpbGxlIiwiYSI6ImNrbDZkb2ppNzFjeXQycW1uOGM0cDY1NmQifQ.-l4ZEOYtpkk39Re3txcSNw',
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [3.7174, 51.0543],
      maxZoom: 20,
      minZoom: 5,
      zoom: 10
    });

// Holds visible airport features for filtering
    let markers: Marker[] = [];

// Create a popup, but don't add it to the map yet.
    const popup = new mapboxgl.Popup({
      closeButton: false
    });

    function addImage(url: string, name: string) {
      map.loadImage(
        url,
        (error: any, image: any) => {
          if (error) {
            throw error;
          }
          map.addImage(name, image as any);
        });
    }

    function addSource(source: Source) {
      const url = 'mapbox://' + source.tileId;
      map.addSource(source.sourceId, {
        type: 'vector',
        url
      });
    }


    map.on('load', () => {

      map.resize();

      addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/manifestation?eventType=betoging&size=64&grey=false', 'manifestIcon');
      addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/workassignment?important=false&size=64&grey=false', 'workassignmentOrangeIcon');
      addImage('http://api.gipod.vlaanderen.be/ws/v1/icon/workassignment?important=true', 'workassignmentRedIcon');

      addSource(servicesCity);
      addSource(servicesProfit);
      addSource(servicesNonProfit);
      addSource(servicesCare);


      map.addLayer({
        id: this.servicesCityLayerId,
        source: servicesCity.sourceId,
        'source-layer': servicesCity.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'visible'
        }
      });

      map.addLayer({
        id: this.servicesProfitLayerId,
        source: servicesProfit.sourceId,
        'source-layer': servicesProfit.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'visible'
        }
      });

      map.addLayer({
        id: this.servicesNonProfitLayerId,
        source: servicesNonProfit.sourceId,
        'source-layer': servicesNonProfit.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'visible'
        }
      });

      map.addLayer({
        id: this.servicesCareLayerId,
        source: servicesCare.sourceId,
        'source-layer': servicesCare.tileName,
        type: 'symbol',
        layout: {
          'icon-image': 'manifestIcon',
          'icon-size': 0.35,
          'icon-allow-overlap': true,
          visibility: 'visible'
        }
      });


      map.on('moveend', () => {
        // @ts-ignore
        const features: Marker[] =  map.queryRenderedFeatures({layers: this.layers});

        if (features) {
          markers = features;
        }
      });

      map.on('mousemove', this.servicesProfitLayerId, (e: any) => {
// Change the cursor style as a UI indicator.
        map.getCanvas().style.cursor = 'pointer';

// Populate the popup and set its coordinates based on the feature.
        if (!e.features) {
          return;
        }
        const feature = e.features[0];
        const geometry = feature.geometry as any;
        popup
          .setLngLat(geometry.coordinates)
          .setText(feature.properties!.description)
          .addTo(map);
      });


      map.on('mouseleave', this.servicesProfitLayerId, () => {
        map.getCanvas().style.cursor = '';
        popup.remove();
      });

      map.on('click', this.servicesCityLayerId, (e: any) => {
// Change the cursor style as a UI indicator.
        map.getCanvas().style.cursor = 'pointer';

// Populate the popup and set its coordinates based on the feature.
        if (!e.features) {
          return;
        }
        const feature: Marker = e.features[0];
        popup
          .setLngLat([feature.geometry.coordinates[0], feature.geometry.coordinates[1]])
          .setText(
            feature.properties.name
          )
          .addTo(map);
        this.onClickMarker(feature);
      });


      // enumerate ids of the layers
      const toggleableLayerIds = [this.servicesProfitLayerId, this.servicesNonProfitLayerId,
        this.servicesCareLayerId, this.servicesCityLayerId];

// set up the corresponding toggle button for each layer
      for (const id of toggleableLayerIds) {
        const link = document.createElement('a');
        link.href = '#';
        link.className = 'active';
        link.textContent = id;

        link.onclick = e => {
          // tslint:disable-next-line:no-non-null-assertion
          const clickedLayer = link.textContent!;
          e.preventDefault();
          e.stopPropagation();

          const visibility = map.getLayoutProperty(clickedLayer, 'visibility');

// toggle layer visibility by changing the layout object's visibility property
          if (visibility === 'visible') {
            map.setLayoutProperty(clickedLayer, 'visibility', 'none');
            link.className = '';
          } else {
            link.className = 'active';
            map.setLayoutProperty(clickedLayer, 'visibility', 'visible');
          }
        };
      }
    });
  }
}


