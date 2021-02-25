import webapp2

from rogerthat.mapbox.mapbox_exporter import import_all_services, dataset_to_tileset


class ExportToTilesetHandler(webapp2.RequestHandler):
    def get(self):
        dataset_to_tileset()
