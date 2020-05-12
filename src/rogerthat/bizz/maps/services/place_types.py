# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.7@@

# 
# from __future__ import unicode_literals
# 
# from mcfw.properties import unicode_list_property, unicode_property, \
#     bool_property, long_list_property, typed_property
# from mcfw.utils import Enum
# from rogerthat.models import BaseServiceProfile
# from rogerthat.to import TO
# from rogerthat.translations import localize
# from typing import Dict, List
# 
# 
# # List from https://developers.google.com/places/supported_types
# class PlaceType(Enum):
#     ACCOUNTING = 'accounting'
#     AIRPORT = 'airport'
#     AMUSEMENT_PARK = 'amusement_park'
#     AQUARIUM = 'aquarium'
#     ART_GALLERY = 'art_gallery'
#     ATM = 'atm'
#     BAKERY = 'bakery'
#     BANK = 'bank'
#     BAR = 'bar'
#     BEAUTY_SALON = 'beauty_salon'
#     BICYCLE_STORE = 'bicycle_store'
#     BOOK_STORE = 'book_store'
#     BOWLING_ALLEY = 'bowling_alley'
#     BUS_STATION = 'bus_station'
#     CAFE = 'cafe'
#     CAMPGROUND = 'campground'
#     CAR_DEALER = 'car_dealer'
#     CAR_RENTAL = 'car_rental'
#     CAR_REPAIR = 'car_repair'
#     CAR_WASH = 'car_wash'
#     CASINO = 'casino'
#     CEMETERY = 'cemetery'
#     CHURCH = 'church'
#     CITY_HALL = 'city_hall'
#     CLOTHING_STORE = 'clothing_store'
#     CONVENIENCE_STORE = 'convenience_store'
#     COURTHOUSE = 'courthouse'
#     DENTIST = 'dentist'
#     DEPARTMENT_STORE = 'department_store'
#     DOCTOR = 'doctor'
#     DRUGSTORE = 'drugstore'
#     ELECTRICIAN = 'electrician'
#     ELECTRONICS_STORE = 'electronics_store'
#     EMBASSY = 'embassy'
#     FIRE_STATION = 'fire_station'
#     FLORIST = 'florist'
#     FUNERAL_HOME = 'funeral_home'
#     FURNITURE_STORE = 'furniture_store'
#     GAS_STATION = 'gas_station'
#     GROCERY_OR_SUPERMARKET = 'grocery_or_supermarket'
#     GYM = 'gym'
#     HAIR_CARE = 'hair_care'
#     HARDWARE_STORE = 'hardware_store'
#     HINDU_TEMPLE = 'hindu_temple'
#     HOME_GOODS_STORE = 'home_goods_store'
#     HOSPITAL = 'hospital'
#     INSURANCE_AGENCY = 'insurance_agency'
#     JEWELRY_STORE = 'jewelry_store'
#     LAUNDRY = 'laundry'
#     LAWYER = 'lawyer'
#     LIBRARY = 'library'
#     LIGHT_RAIL_STATION = 'light_rail_station'
#     LIQUOR_STORE = 'liquor_store'
#     LOCAL_GOVERNMENT_OFFICE = 'local_government_office'
#     LOCKSMITH = 'locksmith'
#     LODGING = 'lodging'
#     MEAL_DELIVERY = 'meal_delivery'
#     MEAL_TAKEAWAY = 'meal_takeaway'
#     MOSQUE = 'mosque'
#     MOVIE_RENTAL = 'movie_rental'
#     MOVIE_THEATER = 'movie_theater'
#     MOVING_COMPANY = 'moving_company'
#     MUSEUM = 'museum'
#     NIGHT_CLUB = 'night_club'
#     PAINTER = 'painter'
#     PARK = 'park'
#     PARKING = 'parking'
#     PET_STORE = 'pet_store'
#     PHARMACY = 'pharmacy'
#     PHYSIOTHERAPIST = 'physiotherapist'
#     PLUMBER = 'plumber'
#     POLICE = 'police'
#     POST_OFFICE = 'post_office'
#     PRIMARY_SCHOOL = 'primary_school'
#     REAL_ESTATE_AGENCY = 'real_estate_agency'
#     RESTAURANT = 'restaurant'
#     ROOFING_CONTRACTOR = 'roofing_contractor'
#     RV_PARK = 'rv_park'
#     SCHOOL = 'school'
#     SECONDARY_SCHOOL = 'secondary_school'
#     SHOE_STORE = 'shoe_store'
#     SHOPPING_MALL = 'shopping_mall'
#     SPA = 'spa'
#     STADIUM = 'stadium'
#     STORAGE = 'storage'
#     STORE = 'store'
#     SUBWAY_STATION = 'subway_station'
#     SUPERMARKET = 'supermarket'
#     SYNAGOGUE = 'synagogue'
#     TAXI_STAND = 'taxi_stand'
#     TOURIST_ATTRACTION = 'tourist_attraction'
#     TRAIN_STATION = 'train_station'
#     TRANSIT_STATION = 'transit_station'
#     TRAVEL_AGENCY = 'travel_agency'
#     UNIVERSITY = 'university'
#     VETERINARY_CARE = 'veterinary_care'
#     ZOO = 'zoo'
#     # custom items
#     ASSOCIATION = 'association'
#     BUTCHER = 'butcher'
#     NURSE = 'nurse'
# 
# 
# class GroupType(Enum):
#     ANIMALS = 'animals'
#     CAR = 'car'
#     CLOTHING = 'clothing'
#     DRINKS = 'drinks'
#     FOOD = 'food'
#     HEALTH = 'health'
#     RELIGION = 'religion'
#     POI = 'point_of_interest'
# 
# 
# def get_icon_color(icon_id):
#     icon_color_1 = '#f07b0e'  # orange
#     icon_color_2 = '#c71906'  # red
#     icon_color_3 = '#1e1af0'  # blue
#     icon_color_4 = '#18990f'  # green
#     icon_color_5 = '#ccc610'  # yellow
#     if not icon_id:
#         return icon_color_5
# 
#     if icon_id.startswith('fa1-') or icon_id.startswith('c1-'):
#         return icon_color_1
#     if icon_id.startswith('fa2-') or icon_id.startswith('c2-'):
#         return icon_color_2
#     if icon_id.startswith('fa3-') or icon_id.startswith('c3-'):
#         return icon_color_3
#     if icon_id.startswith('fa4-') or icon_id.startswith('c4-'):
#         return icon_color_4
#     if icon_id.startswith('fa5-') or icon_id.startswith('c5-'):
#         return icon_color_5
#     return icon_color_5
# 
# 
# def get_place_label(place_details, language):
#     if not place_details.title:
#         raise Exception('Title not set for place type %s', place_details.to_dict())
#     return localize(language, place_details.title)
# 
# 
# def get_suggest_place_labels(place_details, language):
#     translations = set()
#     for alias in place_details.aliases:
#         if alias.languages and language not in alias.languages:
#             continue
#         for key in alias.keys:
#             transl = localize(language, key, language_fallback=False)
#             if not transl:
#                 continue
#             translations.add(transl)
#     for group_type in place_details.groups:
#         group_details = PLACE_DETAILS.get(group_type, None)
#         if not group_details:
#             continue
#         if group_details.replaced_by:
#             continue
#         translations.update(get_suggest_place_labels(group_details, language))
#     return translations
# 
# 
# def get_search_place_labels(place_details, language):
#     translations = set()
#     for alias in place_details.aliases:
#         if alias.languages and language not in alias.languages:
#             continue
#         for key in alias.keys:
#             transl = localize(language, key, language_fallback=False)
#             if not transl:
#                 continue
#             translations.add(transl)
#     return list(translations)
# 
# 
# class PlaceDetailAliases(TO):
#     languages = unicode_list_property('languages', default=[]) # empty = all languages
#     keys = unicode_list_property('keys', default=[])
# 
# 
# class PlaceDetails(TO):
#     visible = bool_property('visible', default=True)
#     replaced_by = unicode_property('replaced_by', default=None)
#     fa_icon = unicode_property('fa_icon', default=None)
#     png_icon = unicode_property('png_icon', default='fa5-map-marker')
#     title = unicode_property('title', default=None)
#     aliases = typed_property('aliases', PlaceDetailAliases, True, default=[])
#     groups = unicode_list_property('groups', default=[])
#     organization_types = long_list_property('organization_types', default=[])
# 
# 
# PLACE_DETAILS = {
#     PlaceType.ACCOUNTING: PlaceDetails(png_icon='fa1-briefcase',
#                                        title='accounting',
#                                        aliases=[PlaceDetailAliases(keys=['accounting', 'accountant', 'accountancy'])],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.AIRPORT: PlaceDetails(png_icon='fa1-plane',
#                                     title='airport',
#                                     aliases=[PlaceDetailAliases(keys=['airport'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.AMUSEMENT_PARK: PlaceDetails(png_icon='fa5-smile-o',
#                                            title='amusement_park',
#                                            aliases=[PlaceDetailAliases(keys=['amusement_park', 'theme_park'])],
#                                            groups=[GroupType.POI]),
#     PlaceType.AQUARIUM: PlaceDetails(replaced_by=PlaceType.AMUSEMENT_PARK),
#     PlaceType.ART_GALLERY: PlaceDetails(png_icon='fa5-paint-brush',
#                                         title='art_gallery',
#                                         aliases=[PlaceDetailAliases(keys=['art_gallery', 'art', 'gallery'])],
#                                         groups=[GroupType.POI]),
#     PlaceType.ATM: PlaceDetails(png_icon='fa5-money',
#                                 title='atm',
#                                 aliases=[PlaceDetailAliases(keys=['atm', 'cash'])],
#                                 groups=[GroupType.POI]),
#     PlaceType.BAKERY: PlaceDetails(fa_icon='fa-birthday-cake',
#                                    png_icon='fa1-birthday-cake',
#                                    title='bakery',
#                                    aliases=[PlaceDetailAliases(keys=['bakery', 'baker', 'bread'])],
#                                    groups=[GroupType.FOOD],
#                                    organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.BANK: PlaceDetails(png_icon='fa5-credit-card-alt',
#                                  title='bank',
#                                  aliases=[PlaceDetailAliases(keys=['bank', 'bank_branch'])],
#                                  groups=[GroupType.POI]),
#     PlaceType.BAR: PlaceDetails(fa_icon='fa-glass',
#                                 png_icon='fa1-glass',
#                                 title='bar',
#                                 aliases=[PlaceDetailAliases(keys=['bar', 'pub', 'cocktail'])],
#                                 groups=[GroupType.DRINKS],
#                                 organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.BEAUTY_SALON: PlaceDetails(png_icon='c1-beauty-nail',
#                                          title='beauty_salon',
#                                          aliases=[PlaceDetailAliases(keys=['beauty_salon', 'manicure', 'pedicure'])],
#                                          organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.BICYCLE_STORE: PlaceDetails(png_icon='fa1-bicycle',
#                                           title='bicycle_store',
#                                           aliases=[PlaceDetailAliases(keys=['bicycle_store', 'bicycle'])],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.BOOK_STORE: PlaceDetails(png_icon='fa1-book',
#                                        title='book_store',
#                                        aliases=[PlaceDetailAliases(keys=['book_store', 'books', 'reading'])],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.BOWLING_ALLEY: PlaceDetails(png_icon='c5-bowling',
#                                           title='bowling_alley',
#                                           aliases=[PlaceDetailAliases(keys=['bowling_alley', 'bowling'])],
#                                           groups=[GroupType.POI]),
#     PlaceType.BUS_STATION: PlaceDetails(png_icon='fa5-bus',
#                                         title='bus_station',
#                                         aliases=[PlaceDetailAliases(keys=['bus_station'])],
#                                         groups=[GroupType.POI]),
#     PlaceType.CAFE: PlaceDetails(png_icon='fa1-coffee',
#                                  title='cafe',
#                                  aliases=[PlaceDetailAliases(keys=['cafe'])],
#                                  groups=[GroupType.DRINKS],
#                                  organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CAMPGROUND: PlaceDetails(png_icon='fa5-free-code-camp',
#                                        title='campground',
#                                        aliases=[PlaceDetailAliases(keys=['campground'])],
#                                        groups=[GroupType.POI]),
#     PlaceType.CAR_DEALER: PlaceDetails(png_icon='fa1-car',
#                                        title='car_dealer',
#                                        aliases=[PlaceDetailAliases(keys=['car_dealer'])],
#                                        groups=[GroupType.CAR],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CAR_RENTAL: PlaceDetails(png_icon='fa1-car',
#                                        title='car_rental',
#                                        aliases=[PlaceDetailAliases(keys=['car_rental'])],
#                                        groups=[GroupType.CAR],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CAR_REPAIR: PlaceDetails(png_icon='fa1-car',
#                                        title='car_repair',
#                                        aliases=[PlaceDetailAliases(keys=['car_repair'])],
#                                        groups=[GroupType.CAR],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CAR_WASH: PlaceDetails(png_icon='c1-carwash',
#                                      title='car_wash',
#                                      aliases=[PlaceDetailAliases(keys=['car_wash'])],
#                                      groups=[GroupType.CAR],
#                                      organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CASINO: PlaceDetails(png_icon='c1-casino',
#                                    title='casino',
#                                    aliases=[PlaceDetailAliases(keys=['casino'])],
#                                    organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CEMETERY: PlaceDetails(png_icon='c5-graveyard',
#                                      title='cemetery',
#                                      aliases=[PlaceDetailAliases(keys=['cemetery', 'graveyard'])],
#                                      groups=[GroupType.POI]),
#     PlaceType.CHURCH: PlaceDetails(png_icon='c5-church',
#                                    title='church',
#                                    aliases=[PlaceDetailAliases(keys=['church'])],
#                                    groups=[GroupType.POI, GroupType.RELIGION]),
#     PlaceType.CITY_HALL: PlaceDetails(png_icon='fa5-university',
#                                       title='city_hall',
#                                       aliases=[PlaceDetailAliases(keys=['city_hall', 'town_hall'])]),
#     PlaceType.CLOTHING_STORE: PlaceDetails(fa_icon='fa-shopping-bag',
#                                            png_icon='fa1-shopping-bag',
#                                            title='clothing_store',
#                                            aliases=[PlaceDetailAliases(keys=['clothing_store'])],
#                                            sub_groups=[GroupType.CLOTHING],
#                                            organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.CONVENIENCE_STORE: PlaceDetails(replaced_by=PlaceType.SUPERMARKET),
#     PlaceType.COURTHOUSE: PlaceDetails(png_icon='fa5-gavel',
#                                        title='courthouse',
#                                        aliases=[PlaceDetailAliases(keys=['courthouse', 'justice'])],
#                                        groups=[GroupType.POI]),
#     PlaceType.DENTIST: PlaceDetails(png_icon='fa2-user-md',
#                                     title='dentist',
#                                     aliases=[PlaceDetailAliases(keys=['dentist', 'teeth', 'tooth'])],
#                                     groups=[GroupType.HEALTH],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_EMERGENCY]),
#     PlaceType.DEPARTMENT_STORE: PlaceDetails(replaced_by=PlaceType.SUPERMARKET),
#     PlaceType.DOCTOR: PlaceDetails(fa_icon='fa-stethoscope',
#                                    png_icon='fa2-stethoscope',
#                                    title='doctor',
#                                    aliases=[PlaceDetailAliases(keys=['doctor', 'physician', 'therapist'])],
#                                    groups=[GroupType.HEALTH],
#                                    organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_EMERGENCY]),
#     PlaceType.DRUGSTORE: PlaceDetails(replaced_by=PlaceType.PHARMACY),
#     PlaceType.ELECTRICIAN: PlaceDetails(png_icon='c1-craftsman',
#                                         title='electrician',
#                                         aliases=[PlaceDetailAliases(keys=['electrician'])],
#                                         organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.ELECTRONICS_STORE: PlaceDetails(png_icon='c1-electronics-store',
#                                               title='electronics_store',
#                                               aliases=[PlaceDetailAliases(keys=['electronics_store'])]),
#     PlaceType.EMBASSY: PlaceDetails(png_icon='fa4-flag',
#                                     title='embassy',
#                                     aliases=[PlaceDetailAliases(keys=['embassy'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_CITY]),
#     PlaceType.FIRE_STATION: PlaceDetails(png_icon='fa4-fire-extinguisher',
#                                          title='fire_station',
#                                          aliases=[PlaceDetailAliases(keys=['fire_station'])],
#                                          organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_CITY]),
#     PlaceType.FLORIST: PlaceDetails(png_icon='c1-flower',
#                                     title='florist',
#                                     aliases=[PlaceDetailAliases(keys=['florist', 'flowers'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.FUNERAL_HOME: PlaceDetails(png_icon='c1-funerals-insurance',
#                                          title='funeral_home',
#                                          aliases=[PlaceDetailAliases(keys=['funeral_home', 'funeral', 'undertaker'])],
#                                          organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.FURNITURE_STORE: PlaceDetails(png_icon='c1-furniture-store',
#                                             title='furniture_store',
#                                             aliases=[PlaceDetailAliases(keys=['furniture_store', 'furniture'])],
#                                             organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.GAS_STATION: PlaceDetails(png_icon='c5-gas-station',
#                                         title='gas_station',
#                                         aliases=[PlaceDetailAliases(keys=['gas_station', 'petrol_station'])],
#                                         groups=[GroupType.POI]),
#     PlaceType.GROCERY_OR_SUPERMARKET: PlaceDetails(fa_icon='fa-shopping-basket',
#                                                    png_icon='fa1-shopping-basket',
#                                                    title='groceries',
#                                                    aliases=[PlaceDetailAliases(keys=['groceries', 'grocery', 'supermarket'])],
#                                                    groups=[GroupType.FOOD],
#                                                    organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.GYM: PlaceDetails(png_icon='c1-gym',
#                                 title='fitness',
#                                 aliases=[PlaceDetailAliases(keys=['fitness', 'gym', 'sport_club'])],
#                                 organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.HAIR_CARE: PlaceDetails(png_icon='c1-hairdresser',
#                                       title='hair_care',
#                                       aliases=[PlaceDetailAliases(keys=['hair_care', 'hairdresser', 'barber'])],
#                                       organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.HARDWARE_STORE: PlaceDetails(png_icon='fa1-television',
#                                            title='multi_media',
#                                            aliases=[PlaceDetailAliases(keys=['multi_media', 'hardware_store', 'phone', 'laptop', 'computer'])],
#                                            organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.HINDU_TEMPLE: PlaceDetails(png_icon='c5-religion-faith',
#                                          title='hindu_temple',
#                                          aliases=[PlaceDetailAliases(keys=['hindu_temple'])],
#                                          groups=[GroupType.POI, GroupType.RELIGION]),
#     PlaceType.HOME_GOODS_STORE: PlaceDetails(png_icon='c1-furniture-shopping',
#                                              title='home_goods_store',
#                                              aliases=[PlaceDetailAliases(keys=['home_goods_store'])],
#                                              organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.HOSPITAL: PlaceDetails(png_icon='fa2-hospital-o',
#                                      title='hospital',
#                                      aliases=[PlaceDetailAliases(keys=['hospital', 'clinic', 'healthcare', 'specialist'])],
#                                      groups=[GroupType.HEALTH],
#                                      organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_EMERGENCY]),
#     PlaceType.INSURANCE_AGENCY: PlaceDetails(png_icon='fa1-building',
#                                              title='insurance_agency',
#                                              aliases=[PlaceDetailAliases(keys=['insurance_agency', 'insurance', 'insurer'])],
#                                              organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.JEWELRY_STORE: PlaceDetails(png_icon='c1-jewelry',
#                                           title='jewelry_store',
#                                           aliases=[PlaceDetailAliases(keys=['jewelry_store', 'jewellery'])],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.LAUNDRY: PlaceDetails(png_icon='c1-laundry',
#                                     title='laundry',
#                                     aliases=[PlaceDetailAliases(keys=['laundry', 'laundry_room'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.LAWYER: PlaceDetails(png_icon='fa1-gavel',
#                                    title='lawyer',
#                                    aliases=[PlaceDetailAliases(keys=['lawyer', 'jurist', 'legist', 'justice'])],
#                                    organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.LIBRARY: PlaceDetails(png_icon='fa4-book',
#                                     title='library',
#                                     aliases=[PlaceDetailAliases(keys=['library', 'books'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_CITY]),
#     PlaceType.LIGHT_RAIL_STATION: PlaceDetails(replaced_by=PlaceType.TRAIN_STATION),
#     PlaceType.LIQUOR_STORE: PlaceDetails(png_icon='c1-liquor',
#                                          title='liquor_store',
#                                          aliases=[PlaceDetailAliases(keys=['liquor_store', 'beverage_center'])],
#                                          organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.LOCAL_GOVERNMENT_OFFICE: PlaceDetails(png_icon='fa4-university',
#                                                     title='local_government_office',
#                                                     aliases=[PlaceDetailAliases(keys=['local_government_office', 'city_hall', 'town_hall'])],
#                                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_CITY]),
#     PlaceType.LOCKSMITH: PlaceDetails(png_icon='fa1-unlock-alt',
#                                       title='locksmith',
#                                       aliases=[PlaceDetailAliases(keys=['locksmith'])],
#                                       organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.LODGING: PlaceDetails(fa_icon='fa-bed',
#                                     png_icon='fa1-bed',
#                                     title='lodging',
#                                     aliases=[PlaceDetailAliases(keys=['lodging', 'Hotel', 'b_and_b', 'overnight_stay'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.MEAL_DELIVERY: PlaceDetails(png_icon='fa1-cutlery',
#                                           title='meal_delivery',
#                                           aliases=[PlaceDetailAliases(keys=['meal_delivery'])],
#                                           groups=[GroupType.FOOD],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.MEAL_TAKEAWAY: PlaceDetails(png_icon='fa1-cutlery',
#                                           title='meal_takeaway',
#                                           aliases=[PlaceDetailAliases(keys=['meal_takeaway'])],
#                                           groups=[GroupType.FOOD],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.MOSQUE: PlaceDetails(png_icon='c5-religion-faith',
#                                    title='mosque',
#                                    aliases=[PlaceDetailAliases(keys=['mosque'])],
#                                    groups=[GroupType.POI, GroupType.RELIGION]),
#     PlaceType.MOVIE_RENTAL: PlaceDetails(png_icon='fa1-film',
#                                          title='movie_rental',
#                                          aliases=[PlaceDetailAliases(keys=['movie_rental', 'movies'])],
#                                          organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.MOVIE_THEATER: PlaceDetails(png_icon='fa1-film',
#                                           title='movie_theater',
#                                           aliases=[PlaceDetailAliases(keys=['movie_theater', 'movies'])],
#                                           groups=[GroupType.POI],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.MOVING_COMPANY: PlaceDetails(png_icon='fa1-truck',
#                                            title='moving_company',
#                                            aliases=[PlaceDetailAliases(keys=['moving_company', 'moving'])],
#                                            organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.MUSEUM: PlaceDetails(png_icon='fa5-paint-brush',
#                                    title='museum',
#                                    aliases=[PlaceDetailAliases(keys=['museum', 'art'])]),
#     PlaceType.NIGHT_CLUB: PlaceDetails(png_icon='c1-nightclub',
#                                        title='night_club',
#                                        aliases=[PlaceDetailAliases(keys=['night_club', 'disco'])],
#                                        groups=[GroupType.POI],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.PAINTER: PlaceDetails(png_icon='fa1-paint-brush',
#                                     title='painter',
#                                     aliases=[PlaceDetailAliases(keys=['painter', 'paint'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.PARK: PlaceDetails(png_icon='c5-park',
#                                  title='park',
#                                  aliases=[PlaceDetailAliases(keys=['park'])],
#                                  groups=[GroupType.POI]),
#     PlaceType.PARKING: PlaceDetails(png_icon='c5-parking',
#                                     title='parking',
#                                     aliases=[PlaceDetailAliases(keys=['parking', 'car_park'])],
#                                     groups=[GroupType.CAR]),
#     PlaceType.PET_STORE: PlaceDetails(png_icon='fa1-paw',
#                                       title='pet_store',
#                                       aliases=[PlaceDetailAliases(keys=['pet_store', 'pets'])],
#                                       groups=[GroupType.POI, GroupType.ANIMALS],
#                                       organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.PHARMACY: PlaceDetails(fa_icon='fa-medkit',
#                                      png_icon='fa2-medkit',
#                                      title='pharmacy',
#                                      aliases=[PlaceDetailAliases(keys=['pharmacy', 'medicines', 'chemist', 'drugstore'])],
#                                      groups=[GroupType.HEALTH],
#                                      organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_EMERGENCY]),
#     PlaceType.PHYSIOTHERAPIST: PlaceDetails(png_icon='fa2-stethoscope',
#                                             title='physiotherapist',
#                                             aliases=[PlaceDetailAliases(keys=['physiotherapist'])],
#                                             groups=[GroupType.HEALTH],
#                                             organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_EMERGENCY]),
#     PlaceType.PLUMBER: PlaceDetails(png_icon='fa1-wrench',
#                                     title='plumber',
#                                     aliases=[PlaceDetailAliases(keys=['plumber'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.POLICE: PlaceDetails(png_icon='c4-police',
#                                    title='police',
#                                    aliases=[PlaceDetailAliases(keys=['police'])],
#                                    organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_CITY]),
#     PlaceType.POST_OFFICE: PlaceDetails(png_icon='fa5-envelope',
#                                         title='post_office',
#                                         aliases=[PlaceDetailAliases(keys=['post_office', 'post', 'letters'])],
#                                         groups=[GroupType.POI]),
#     PlaceType.PRIMARY_SCHOOL: PlaceDetails(replaced_by=PlaceType.SCHOOL),
#     PlaceType.REAL_ESTATE_AGENCY: PlaceDetails(png_icon='fa1-building-o',
#                                                title='real_estate_agency',
#                                                aliases=[PlaceDetailAliases(keys=['real_estate_agency'])],
#                                                organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.RESTAURANT: PlaceDetails(fa_icon='fa-cutlery',
#                                        png_icon='fa1-cutlery',
#                                        title='restaurant',
#                                        aliases=[PlaceDetailAliases(keys=['restaurant', 'bistro'])],
#                                        groups=[GroupType.FOOD],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.ROOFING_CONTRACTOR: PlaceDetails(png_icon='fa1-wrench',
#                                                title='roofing_contractor',
#                                                aliases=[PlaceDetailAliases(keys=['roofing_contractor'])],
#                                                organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.RV_PARK: PlaceDetails(png_icon='c1-rv',
#                                     title='rv_park',
#                                     aliases=[PlaceDetailAliases(keys=['rv_park'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.SCHOOL: PlaceDetails(png_icon='fa5-graduation-cap',
#                                    title='school',
#                                    aliases=[PlaceDetailAliases(keys=['school', 'primary_school', 'secondary_school', 'university'])],
#                                    groups=[GroupType.POI]),
#     PlaceType.SECONDARY_SCHOOL: PlaceDetails(replaced_by=PlaceType.SCHOOL),
#     PlaceType.SHOE_STORE: PlaceDetails(png_icon='c1-shoe',
#                                        title='shoe_store',
#                                        aliases=[PlaceDetailAliases(keys=['shoe_store', 'shoes'])],
#                                        groups=[GroupType.CLOTHING],
#                                        organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.SHOPPING_MALL: PlaceDetails(png_icon='fa1-shopping-bag',
#                                           title='shopping_mall',
#                                           aliases=[PlaceDetailAliases(keys=['shopping_mall', 'outlet'])],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.SPA: PlaceDetails(png_icon='c1-wellness',
#                                 title='spa',
#                                 aliases=[PlaceDetailAliases(keys=['spa', 'wellness'])],
#                                 organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.STADIUM: PlaceDetails(png_icon='c1-stadium',
#                                     title='stadium',
#                                     aliases=[PlaceDetailAliases(keys=['stadium'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.STORAGE: PlaceDetails(png_icon='fa1-archive',
#                                     title='storage',
#                                     aliases=[PlaceDetailAliases(keys=['storage'])],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.STORE: PlaceDetails(replaced_by=PlaceType.SUPERMARKET),
#     PlaceType.SUBWAY_STATION: PlaceDetails(replaced_by=PlaceType.TRAIN_STATION),
#     PlaceType.SUPERMARKET: PlaceDetails(png_icon='fa1-cart-arrow-down',
#                                         title='supermarket',
#                                         aliases=[PlaceDetailAliases(keys=['supermarket', 'store', 'convenience_store', 'department_store'])],
#                                         groups=[GroupType.FOOD],
#                                         organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.SYNAGOGUE: PlaceDetails(png_icon='c5-religion-faith',
#                                       title='synagogue',
#                                       aliases=[PlaceDetailAliases(keys=['synagogue'])],
#                                       groups=[GroupType.POI, GroupType.RELIGION]),
#     PlaceType.TAXI_STAND: PlaceDetails(png_icon='fa5-taxi',
#                                        title='taxi_stand',
#                                        aliases=[PlaceDetailAliases(keys=['taxi_stand', 'cab'])],
#                                        groups=[GroupType.POI, GroupType.CAR]),
#     PlaceType.TOURIST_ATTRACTION: PlaceDetails(png_icon='c5-amusement_park',
#                                                title='tourist_attraction',
#                                                aliases=[PlaceDetailAliases(keys=['tourist_attraction'])],
#                                                groups=[GroupType.POI]),
#     PlaceType.TRAIN_STATION: PlaceDetails(png_icon='fa5-train',
#                                           title='train_station',
#                                           aliases=[PlaceDetailAliases(keys=['train_station', 'subway_station', 'light_rail_station'])],
#                                           groups=[GroupType.POI]),
#     PlaceType.TRANSIT_STATION: PlaceDetails(png_icon='fa5-terminal',
#                                             title='transit_station',
#                                             aliases=[PlaceDetailAliases(keys=['transit_station'])],
#                                             groups=[GroupType.POI]),
#     PlaceType.TRAVEL_AGENCY: PlaceDetails(png_icon='fa1-plane',
#                                           title='travel_agency',
#                                           aliases=[PlaceDetailAliases(keys=['travel_agency', 'travel'])],
#                                           organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.UNIVERSITY: PlaceDetails(replaced_by=PlaceType.SCHOOL),
#     PlaceType.VETERINARY_CARE: PlaceDetails(png_icon='fa1-heartbeat',
#                                             title='veterinary_care',
#                                             aliases=[PlaceDetailAliases(keys=['veterinary_care', 'veterinarian'])],
#                                             groups=[GroupType.HEALTH, GroupType.ANIMALS],
#                                             organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.ZOO: PlaceDetails(png_icon='fa5-paw',
#                                 title='zoo',
#                                 aliases=[PlaceDetailAliases(keys=['zoo'])],
#                                 groups=[GroupType.POI, GroupType.ANIMALS]),
#     # custom items
#     PlaceType.ASSOCIATION: PlaceDetails(fa_icon='fa-connectdevelop',
#                                         png_icon='fa5-connectdevelop',
#                                         title='Associations',
#                                         aliases=[PlaceDetailAliases(keys=['Associations', 'youth_club', 'sports_club', 'free_time', 'hobby'])]),
#     PlaceType.BUTCHER: PlaceDetails(fa_icon='fa-cutlery',
#                                     png_icon='c1-butcher',
#                                     title='butcher',
#                                     aliases=[PlaceDetailAliases(keys=['butcher']),
#                                                   PlaceDetailAliases(languages=['nl'],
#                                                                           keys=['butchery', 'butcher_addition_1'])],
#                                     groups=[GroupType.FOOD],
#                                     organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     PlaceType.NURSE: PlaceDetails(png_icon='fa1-user-md',
#                                   title='nurse',
#                                   aliases=[PlaceDetailAliases(keys=['nurse', 'male_nurse', 'home_nursing'])],
#                                   groups=[GroupType.HEALTH],
#                                   organization_types=[BaseServiceProfile.ORGANIZATION_TYPE_PROFIT]),
#     # group items
#     GroupType.ANIMALS: PlaceDetails(visible=False,
#                                     title='animals',
#                                     aliases=[PlaceDetailAliases(keys=['animals'])]),
#     GroupType.CAR: PlaceDetails(visible=False,
#                                 title='car',
#                                 aliases=[PlaceDetailAliases(keys=['car'])]),
#     GroupType.CLOTHING: PlaceDetails(visible=False,
#                                      title='clothing',
#                                      aliases=[PlaceDetailAliases(keys=['clothing'])]),
#     GroupType.DRINKS: PlaceDetails(visible=False,
#                                    title='drinks',
#                                    aliases=[PlaceDetailAliases(keys=['drinks'])]),
#     GroupType.FOOD: PlaceDetails(visible=False,
#                                  title='food',
#                                  aliases=[PlaceDetailAliases(keys=['food'])]),
#     GroupType.HEALTH: PlaceDetails(visible=False,
#                                  fa_icon='fa-medkit',
#                                  title='Care',
#                                  aliases=[PlaceDetailAliases(keys=['Care'])]),
#     GroupType.RELIGION: PlaceDetails(visible=False,
#                                      title='faith',
#                                    aliases=[PlaceDetailAliases(keys=['faith', 'pray', 'place_of_prayer'])]),
#     GroupType.POI: PlaceDetails(visible=False,
#                               fa_icon='fa-map-marker',
#                               title='poi',
#                               aliases=[PlaceDetailAliases(keys=['poi'])]),
# } # type: Dict[str, PlaceDetails]
