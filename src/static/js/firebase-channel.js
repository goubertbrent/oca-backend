function FirebaseChannel(config, serviceIdentity, customToken, basePath, paths, onConnected, onMessage, onError) {
    this.customToken = customToken;
    this.basePath = basePath;
    this.paths = paths;
    this.onConnected = onConnected;
    this.onMessage = onMessage;
    this.onError = onError;
    this.serviceIdentity = serviceIdentity;

    firebase.initializeApp(config);
    this.initTime = parseInt(new Date().getTime() / 1000);
}


FirebaseChannel.prototype = {
    connect: function() {
        firebase.auth().signInWithCustomToken(this.customToken).then(this.connected.bind(this)).catch(this.onError.bind(this));
    },

    connected: function() {
        this.onConnected();
        this.setupHandlers();
    },

    valueChanged: function(data) {
        var value = data.val();
        if(value && value.timestamp >= this.initTime) {
            var service_identity = value.service_identity;
            if(service_identity && service_identity !== this.serviceIdentity) {
                return;
            }
            this.onMessage(value);
        }
    },

    setupHandlers: function() {
        var self = this;
        $.each(self.paths, function(i, path) {
            var nodeRef = firebase.database().ref(self.basePath).child(path);
            nodeRef.on('value', self.valueChanged.bind(self));
        });
    },


};
