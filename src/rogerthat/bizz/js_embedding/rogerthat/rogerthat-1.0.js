/*
 * Copyright 2020 Green Valley Belgium NV
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @@license_version:1.7@@
 */

var ROGERTHAT_SCHEME = "rogerthat://";

var MAJOR_VERSION = 0;
var MINOR_VERSION = 1;
var PATCH_VERSION = 0;
var FEATURE_CHECKING = 0;
var FEATURE_SUPPORTED = 1;
var FEATURE_NOT_SUPPORTED = 2;

var PROXIMITY_UNKNOWN = 0;
var PROXIMITY_IMMEDIATE = 1;
var PROXIMITY_NEAR = 2;
var PROXIMITY_FAR = 3;

var _dummy = function () {
};

_loadPolyfills();

var rogerthat = {
    _shouldCallReady: false,
    MAJOR_VERSION: MAJOR_VERSION,
    MINOR_VERSION: MINOR_VERSION,
    PATCH_VERSION: PATCH_VERSION,
    PROXIMITY_UNKNOWN: PROXIMITY_UNKNOWN,
    PROXIMITY_IMMEDIATE: PROXIMITY_IMMEDIATE,
    PROXIMITY_NEAR: PROXIMITY_NEAR,
    PROXIMITY_FAR: PROXIMITY_FAR,
    VERSION: MAJOR_VERSION + "." + MINOR_VERSION + "." + PATCH_VERSION,
    util: {
        uuid: function () {
            var S4 = function () {
                return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
            };
            return (S4() + S4() + "-" + S4() + "-" + S4() + "-" + S4() + "-" + S4() + S4() + S4());
        },
        _translations: {
            defaultLanguage: "en",
            // eg; "Name": { "fr": "Nom", "nl": "Naam" }
            values: {}
        },
        _translateHTML: function () {
            $("x-rogerthat-t").each(function (i, elem) {
                var t = $(elem);
                var html = t.html();
                t.replaceWith(rogerthat.util.translate(html));
            });
        },
        translate: function (key, parameters) {
            var language = rogerthat.user.language || rogerthat.util._translations.defaultLanguage;
            var translation = undefined;
            if (language != rogerthat.util._translations.defaultLanguage) {
                var translationSet = rogerthat.util._translations.values[key];
                if (translationSet) {
                    translation = translationSet[language];
                    if (translation === undefined) {
                        if (language.indexOf('_') != -1) {
                            language = language.split('_')[0];
                            translation = translationSet[language];
                        }
                    }
                }
            }

            if (translation == undefined) {
                // language is defaultLanguage / key is missing / key is not translated
                translation = key;
            }

            if (parameters) {
                $.each(parameters, function (param, value) {
                    translation = translation.replace('%(' + param + ')s', value);
                });
            }
            return translation;
        }
    },
    features: {
        base64URI: FEATURE_SUPPORTED,
        backgroundSize: FEATURE_SUPPORTED,
        callback: undefined
    },
    camera: {
        FRONT: "front",
        BACK: "back"
    },
    security: {},
    message: {},
    news: {}
};

function _checkCapabilities() {
    // deprecated - has been supported for years everywhere
    if (rogerthat.features.callback) {
        rogerthat.features.callback('base64URI');
        rogerthat.features.callback('backgroundSize');
    }
}

_checkCapabilities();

/*-
 * Generate methods to be able to subscribe the callbacks.
 * eg.
 * rogerthat.callbacks.ready(function () {
 *     console.log("rogerthat lib ready!");
 * });
 */
var _generateCallbacksRegister = function(callbacks) {
    var callbacksRegister = {};
    $.each(callbacks, function(i) {
        callbacksRegister[i] = function(callback) {
            callbacks[i] = callback;
            if (i === 'ready' && rogerthat._shouldCallReady) {
                callback();
                delete rogerthat._shouldCallReady;
            }
        };
    });
    return callbacksRegister;
};

var _callRogerthat = function(action, parameters) {
    var log = action !== 'log/';
    var method = typeof __rogerthat__ !== 'undefined' && __rogerthat__.version !== undefined
            && __rogerthat__.version() >= 1 ? 'invoke' : 'window.location';
    if (method !== 'invoke') {
        var completeUrl = ROGERTHAT_SCHEME + action;
        if (parameters) {
            var encodeSeperately = true;
            if (!rogerthat.system || !rogerthat.system.appVersion || rogerthat.system.appVersion == "unknown") {
            } else {
            	var appVersion = rogerthat.system.appVersion.split(".").map(function(x) {
                    return parseInt(x);
                });
	            if (rogerthat.system.os == "ios" && appVersion[0] > 1 && appVersion[1] >= 1 && appVersion[2] >= 3015) {
	            	encodeSeperately = false;
	            }
            }
            var params = [];
            if (encodeSeperately) {
            	 $.each(parameters, function(param, value) {
 	            	params.push(param + '=' + encodeURIComponent(value));
 	            });
     		} else {
     			params.push('v=1');
	            params.push('d=' + encodeURIComponent(JSON.stringify(parameters)));
	        }
            if (params.length > 0)
                completeUrl += '?' + params.join('&');
        }

        if (log)
            console.log("Calling rogerthat with url: " + completeUrl);

        var iframe = document.createElement("IFRAME");
        iframe.setAttribute("src", completeUrl);
        document.documentElement.appendChild(iframe);
        iframe.parentNode.removeChild(iframe);
        iframe = null;

        return;
    }
    var params = parameters ? JSON.stringify(parameters) : null;
    if (log)
        console.log('Calling rogerthat with action ' + action + ' and parameters ' + params);
    __rogerthat__.invoke(action, params);
};

var _createRogerthatLib = function() {
    var uniqueId = 0;
    var resultHandlers = {};

    var registerResultHandler = function(id, onSuccess, onError) {
        resultHandlers[id] = {
            success : onSuccess,
            error : onError
        };
    };

    var userCallbacks = {
        backPressed: _dummy, // overridden by code below
        ready: null,
        onPause: _dummy,
        onResume: _dummy,
        userDataUpdated: _dummy,
        serviceDataUpdated: _dummy,
        qrCodeScanned: _dummy,
        onBackendConnectivityChanged: _dummy,
        newsReceived: _dummy,
        badgeUpdated: _dummy
    };

    var callbacksRegister = _generateCallbacksRegister(userCallbacks);
    callbacksRegister.backPressed = function(callback) {
        _callRogerthat("back/" + (callback ? "" : "un") + "registerListener", null);
        userCallbacks.backPressed = function(requestId) {
            var handled = false;
            if (callback) {
                try {
                    handled = callback() === true;
                } catch (e) {
                    handled = false;
                    console.error(e);
                }
            }
            var crp = {};
            crp.requestId = requestId;
            crp.handled = handled == true;
            _callRogerthat("back/backPressedCallback", crp);
        };
    };

    var getStackTrace = function(e) {
        if (rogerthat.system !== undefined && rogerthat.system.os == "android") {
            var stack = (e.stack + '\n').replace(/^\S[^\(]+?[\n$]/gm, '') //
            .replace(/^\s+(at eval )?at\s+/gm, '') //
            .replace(/^([^\(]+?)([\n$])/gm, '{anonymous}()@$1$2') //
            .replace(/^Object.<anonymous>\s*\(([^\)]+)\)/gm, '{anonymous}()@$1').split('\n');
            stack.pop();
            return stack.join('\n');
        } else {
            return e.stack.replace(/\[native code\]\n/m, '') //
            .replace(/^(?=\w+Error\:).*$\n/m, '') //
            .replace(/^@/gm, '{anonymous}()@');
        }
    };

    var patchConsoleErrorFunction = function() {
        console.error = function(e) {
            console.log(e);
            if (e.stack) {
                e = e.name + ": " + e.message + "\n" + getStackTrace(e);
            }
            var crp = {};
            crp.e = e;
            _callRogerthat("log/", crp);
        };
    };

    var setRogerthatData = function(info) {
        Object.assign(rogerthat, info);

        if (rogerthat.system === undefined) {
            rogerthat.system = {
                os : "unknown",
                version : "unknown",
                appVersion : "unknown"
            };
        }

        rogerthat.user.put = function(data) {
        	var crp = {};
            if (data === undefined) {
            	crp.u = JSON.stringify(rogerthat.user.data);
            } else {
                Object.assign(rogerthat.user.data, data);
            	var smartUpdate = false;
            	if (!rogerthat.system || !rogerthat.system.appVersion || rogerthat.system.appVersion == "unknown") {
                } else {
                	var appVersion = rogerthat.system.appVersion.split(".").map(function(x) {
                        return parseInt(x);
                    });
             		if (rogerthat.system.os == "android" && appVersion[0] > 1 && appVersion[1] >= 1 && appVersion[2] >= 3608) {
             			smartUpdate = true;
             		} else if (rogerthat.system.os == "ios" && appVersion[0] > 1 && appVersion[1] >= 1 && appVersion[2] >= 2517) {
             			smartUpdate = true;
             		}
                }
            	if (smartUpdate) {
	            	crp.smart = true;
	            	crp.u = JSON.stringify(data);
	            } else {
	            	crp.u = JSON.stringify(rogerthat.user.data);
	            }
            }
            _callRogerthat("user/put", crp);
        };
    };

    var setRogerthatFunctions = function() {

        rogerthat.system.onBackendConnectivityChanged = function(onSuccess, onError) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("system/onBackendConnectivityChanged", {
                id : id
            });
        };

        rogerthat.util.isConnectedToInternet = function(onSuccess, onError) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("util/isConnectedToInternet", {
                id : id
            });
        };

        rogerthat.util.playAudio = function(url, onSuccess, onError) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("util/playAudio", {
                id : id,
                url : url
            });
        };

        rogerthat.util.open = function(params, onSuccess, onError) {
	        	if (!params) {
	        		return;
	        	}
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            params.id = id;
            if (params.action_type) {
            		if (params.action_type === "click" || params.action_type === "action") {
            			params.action = sha256(params.action);
                }
            }
            _callRogerthat("util/open", params);
        };

        rogerthat.message.open = function (messageKey, onSuccess, onError) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("message/open", {
                id: id,
                message_key: messageKey
            });
        };

        rogerthat.camera.startScanningQrCode = function(cameraType, onSuccess, onError) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("camera/startScanningQrCode", {
                id : id,
                camera_type : cameraType
            });
        };

        rogerthat.camera.stopScanningQrCode = function(cameraType, onSuccess, onError) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("camera/stopScanningQrCode", {
                id : id,
                camera_type : cameraType
            });
        };

        rogerthat.security.createKeyPair = function(onSuccess, onError, algorithm, name, message, force, seed) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/createKeyPair", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                message : message,
                force : force,
                seed: seed
            });
        };

        rogerthat.security.hasKeyPair = function(onSuccess, onError, algorithm, name, index) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/hasKeyPair", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                key_index : index
            });
        };

        rogerthat.security.getPublicKey = function(onSuccess, onError, algorithm, name, index) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/getPublicKey", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                key_index : index
            });
        };

        rogerthat.security.getSeed = function(onSuccess, onError, algorithm, name, message) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/getSeed", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                message : message
            });
        };

        rogerthat.security.listAddresses = function(onSuccess, onError, algorithm, name) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/listAddresses", {
                id : id,
                key_algorithm : algorithm,
                key_name : name
            });
        };

        rogerthat.security.getAddress = function(onSuccess, onError, algorithm, name, index, message) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/getAddress", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                key_index : index,
                message : message
            });
        };

        rogerthat.security.sign = function(onSuccess, onError, algorithm, name, index, message, payload, forcePin, hashPayload) {
        		if (hashPayload === undefined) {
                hashPayload = true;
            }
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/sign", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                key_index : index,
                message : message,
                payload : payload,
                force_pin : forcePin,
                hash_payload : hashPayload
            });
        };

        rogerthat.security.verify = function(onSuccess, onError, algorithm, name, index, payload, payloadSignature) {
            var id = uniqueId++;
            registerResultHandler(id, onSuccess, onError);
            _callRogerthat("security/verify", {
                id : id,
                key_algorithm : algorithm,
                key_name : name,
                key_index : index,
                payload : payload,
                payload_signature : payloadSignature
            });
        };
    };

    patchConsoleErrorFunction();

    rogerthat._bridgeLogging = function() {
        console = new Object();
        console.log = function(log) {
            var crp = {};
            crp.m = log;
            _callRogerthat("log/", crp);
        };
        console.error = console.log;
        console.warn = console.log;
        console.info = console.log;
        console.debug = console.log;
        patchConsoleErrorFunction();
    };
    rogerthat._setInfo = function(info) {
        setRogerthatData(info);
        setRogerthatFunctions();
        rogerthat.util._translateHTML();
        if (userCallbacks.ready) {
            userCallbacks.ready();
            delete rogerthat._shouldCallReady;
        } else {
            rogerthat._shouldCallReady = true;
        }
    };
    rogerthat._userDataUpdated = function(userData) {
        rogerthat.user.data = userData;
        userCallbacks.userDataUpdated();
    };
    rogerthat._serviceDataUpdated = function(serviceData) {
        rogerthat.service.data = serviceData;
        userCallbacks.serviceDataUpdated();
    };
    rogerthat._onPause = function() {
        userCallbacks.onPause();
    };
    rogerthat._onResume = function() {
        userCallbacks.onResume();
    };
    rogerthat._backPressed = function(requestId) {
        userCallbacks.backPressed(requestId);
    };
    rogerthat._qrCodeScanned = function(result) {
        userCallbacks.qrCodeScanned(result);
    };
    rogerthat._onBackendConnectivityChanged = function(connected) {
        userCallbacks.onBackendConnectivityChanged(connected);
    };
    rogerthat._newsReceived = function(result) {
        userCallbacks.newsReceived(result);
    };
    rogerthat._badgeUpdated = function(result) {
        userCallbacks.badgeUpdated(result);
    };
    rogerthat._setResult = function(requestId, result, error) {
        setTimeout(function() {
            try {
                if (error) {
                    if (resultHandlers[requestId] && resultHandlers[requestId].error) {
                        resultHandlers[requestId].error(error);
                    }
                } else {
                    if (resultHandlers[requestId] && resultHandlers[requestId].success) {
                        resultHandlers[requestId].success(result);
                    }
                }
            } finally {
                resultHandlers[requestId] = undefined;
            }
        }, 1);
    };
    rogerthat.ui = {
        hideKeyboard : function(element) {
            if (rogerthat.system !== undefined && rogerthat.system.os === "android") {
                try {
                    __rogerthat__.hideKeyboard();
                } catch (err) {
                    console.log(err);
                }
            }
        }
    };
    rogerthat.callbacks = callbacksRegister;
};

_createRogerthatLib();

function getStackTrace(e, isAndroid) {
    if (isAndroid) {
        var stack = (e.stack + '\n').replace(/^\S[^\(]+?[\n$]/gm, '').replace(/^\s+(at eval )?at\s+/gm, '').replace(
                /^([^\(]+?)([\n$])/gm, '{anonymous}()@$1$2').replace(/^Object.<anonymous>\s*\(([^\)]+)\)/gm,
                '{anonymous}()@$1').split('\n');
        stack.pop();
        return stack.join('\n');
    } else {
        return e.stack.replace(/\[native code\]\n/m, '').replace(/^(?=\w+Error\:).*$\n/m, '').replace(/^@/gm,
                '{anonymous}()@');
    }
}

window.addEventListener('error', function(evt) {
    var error = "";
    $.each(evt, function(attr, value) {
        error += attr + ": " + value + "\n";
    });
    console.error("Uncaught javascript exception in HTML-app:\n" + error);
});

function _loadPolyfills() {
    if (typeof Object.assign !== 'function') {
        // Must be writable: true, enumerable: false, configurable: true
        Object.defineProperty(Object, "assign", {
            value: function assign(target, varArgs) { // .length of function is 2
                'use strict';
                if (target === null || target === undefined) {
                    throw new TypeError('Cannot convert undefined or null to object');
                }

                var to = Object(target);

                for (var index = 1; index < arguments.length; index++) {
                    var nextSource = arguments[index];

                    if (nextSource !== null && nextSource !== undefined) {
                        for (var nextKey in nextSource) {
                            // Avoid bugs when hasOwnProperty is shadowed
                            if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                                to[nextKey] = nextSource[nextKey];
                            }
                        }
                    }
                }
                return to;
            },
            writable: true,
            configurable: true
        });
    }
}
/**
 * [js-sha256]{@link https://github.com/emn178/js-sha256}
 *
 * @version 0.5.0
 * @author Chen, Yi-Cyuan [emn178@gmail.com]
 * @copyright Chen, Yi-Cyuan 2014-2017
 * @license MIT
 */
function t(t,h){h?(c[0]=c[16]=c[1]=c[2]=c[3]=c[4]=c[5]=c[6]=c[7]=c[8]=c[9]=c[10]=c[11]=c[12]=c[13]=c[14]=c[15]=0,this.blocks=c):this.blocks=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],t?(this.h0=3238371032,this.h1=914150663,this.h2=812702999,this.h3=4144912697,this.h4=4290775857,this.h5=1750603025,this.h6=1694076839,this.h7=3204075428):(this.h0=1779033703,this.h1=3144134277,this.h2=1013904242,this.h3=2773480762,this.h4=1359893119,this.h5=2600822924,this.h6=528734635,this.h7=1541459225),this.block=this.start=this.bytes=0,this.finalized=this.hashed=!1,this.first=!0,this.is224=t}var h="object"==typeof window?window:{},i=!h.JS_SHA256_NO_NODE_JS&&"object"==typeof process&&process.versions&&process.versions.node;i&&(h=global);var s=!h.JS_SHA256_NO_COMMON_JS&&"object"==typeof module&&module.exports,e="function"==typeof define&&define.amd,r="undefined"!=typeof ArrayBuffer,n="0123456789abcdef".split(""),o=[-2147483648,8388608,32768,128],a=[24,16,8,0],f=[1116352408,1899447441,3049323471,3921009573,961987163,1508970993,2453635748,2870763221,3624381080,310598401,607225278,1426881987,1925078388,2162078206,2614888103,3248222580,3835390401,4022224774,264347078,604807628,770255983,1249150122,1555081692,1996064986,2554220882,2821834349,2952996808,3210313671,3336571891,3584528711,113926993,338241895,666307205,773529912,1294757372,1396182291,1695183700,1986661051,2177026350,2456956037,2730485921,2820302411,3259730800,3345764771,3516065817,3600352804,4094571909,275423344,430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,1955562222,2024104815,2227730452,2361852424,2428436474,2756734187,3204031479,3329325298],u=["hex","array","digest","arrayBuffer"],c=[],p=function(h,i){return function(s){return new t(i,!0).update(s)[h]()}},d=function(h){var s=p("hex",h);i&&(s=y(s,h)),s.create=function(){return new t(h)},s.update=function(t){return s.create().update(t)};for(var e=0;e<u.length;++e){var r=u[e];s[r]=p(r,h)}return s},y=function(t,h){var i=require("crypto"),s=require("buffer").Buffer,e=h?"sha224":"sha256",n=function(h){if("string"==typeof h)return i.createHash(e).update(h,"utf8").digest("hex");if(r&&h instanceof ArrayBuffer)h=new Uint8Array(h);else if(void 0===h.length)return t(h);return i.createHash(e).update(new s(h)).digest("hex")};return n};t.prototype.update=function(t){if(!this.finalized){var i="string"!=typeof t;i&&r&&t instanceof h.ArrayBuffer&&(t=new Uint8Array(t));for(var s,e,n=0,o=t.length||0,f=this.blocks;o>n;){if(this.hashed&&(this.hashed=!1,f[0]=this.block,f[16]=f[1]=f[2]=f[3]=f[4]=f[5]=f[6]=f[7]=f[8]=f[9]=f[10]=f[11]=f[12]=f[13]=f[14]=f[15]=0),i)for(e=this.start;o>n&&64>e;++n)f[e>>2]|=t[n]<<a[3&e++];else for(e=this.start;o>n&&64>e;++n)s=t.charCodeAt(n),128>s?f[e>>2]|=s<<a[3&e++]:2048>s?(f[e>>2]|=(192|s>>6)<<a[3&e++],f[e>>2]|=(128|63&s)<<a[3&e++]):55296>s||s>=57344?(f[e>>2]|=(224|s>>12)<<a[3&e++],f[e>>2]|=(128|s>>6&63)<<a[3&e++],f[e>>2]|=(128|63&s)<<a[3&e++]):(s=65536+((1023&s)<<10|1023&t.charCodeAt(++n)),f[e>>2]|=(240|s>>18)<<a[3&e++],f[e>>2]|=(128|s>>12&63)<<a[3&e++],f[e>>2]|=(128|s>>6&63)<<a[3&e++],f[e>>2]|=(128|63&s)<<a[3&e++]);this.lastByteIndex=e,this.bytes+=e-this.start,e>=64?(this.block=f[16],this.start=e-64,this.hash(),this.hashed=!0):this.start=e}return this}},t.prototype.finalize=function(){if(!this.finalized){this.finalized=!0;var t=this.blocks,h=this.lastByteIndex;t[16]=this.block,t[h>>2]|=o[3&h],this.block=t[16],h>=56&&(this.hashed||this.hash(),t[0]=this.block,t[16]=t[1]=t[2]=t[3]=t[4]=t[5]=t[6]=t[7]=t[8]=t[9]=t[10]=t[11]=t[12]=t[13]=t[14]=t[15]=0),t[15]=this.bytes<<3,this.hash()}},t.prototype.hash=function(){var t,h,i,s,e,r,n,o,a,u,c,p=this.h0,d=this.h1,y=this.h2,l=this.h3,b=this.h4,v=this.h5,g=this.h6,w=this.h7,k=this.blocks;for(t=16;64>t;++t)e=k[t-15],h=(e>>>7|e<<25)^(e>>>18|e<<14)^e>>>3,e=k[t-2],i=(e>>>17|e<<15)^(e>>>19|e<<13)^e>>>10,k[t]=k[t-16]+h+k[t-7]+i<<0;for(c=d&y,t=0;64>t;t+=4)this.first?(this.is224?(o=300032,e=k[0]-1413257819,w=e-150054599<<0,l=e+24177077<<0):(o=704751109,e=k[0]-210244248,w=e-1521486534<<0,l=e+143694565<<0),this.first=!1):(h=(p>>>2|p<<30)^(p>>>13|p<<19)^(p>>>22|p<<10),i=(b>>>6|b<<26)^(b>>>11|b<<21)^(b>>>25|b<<7),o=p&d,s=o^p&y^c,n=b&v^~b&g,e=w+i+n+f[t]+k[t],r=h+s,w=l+e<<0,l=e+r<<0),h=(l>>>2|l<<30)^(l>>>13|l<<19)^(l>>>22|l<<10),i=(w>>>6|w<<26)^(w>>>11|w<<21)^(w>>>25|w<<7),a=l&p,s=a^l&d^o,n=w&b^~w&v,e=g+i+n+f[t+1]+k[t+1],r=h+s,g=y+e<<0,y=e+r<<0,h=(y>>>2|y<<30)^(y>>>13|y<<19)^(y>>>22|y<<10),i=(g>>>6|g<<26)^(g>>>11|g<<21)^(g>>>25|g<<7),u=y&l,s=u^y&p^a,n=g&w^~g&b,e=v+i+n+f[t+2]+k[t+2],r=h+s,v=d+e<<0,d=e+r<<0,h=(d>>>2|d<<30)^(d>>>13|d<<19)^(d>>>22|d<<10),i=(v>>>6|v<<26)^(v>>>11|v<<21)^(v>>>25|v<<7),c=d&y,s=c^d&l^u,n=v&g^~v&w,e=b+i+n+f[t+3]+k[t+3],r=h+s,b=p+e<<0,p=e+r<<0;this.h0=this.h0+p<<0,this.h1=this.h1+d<<0,this.h2=this.h2+y<<0,this.h3=this.h3+l<<0,this.h4=this.h4+b<<0,this.h5=this.h5+v<<0,this.h6=this.h6+g<<0,this.h7=this.h7+w<<0},t.prototype.hex=function(){this.finalize();var t=this.h0,h=this.h1,i=this.h2,s=this.h3,e=this.h4,r=this.h5,o=this.h6,a=this.h7,f=n[t>>28&15]+n[t>>24&15]+n[t>>20&15]+n[t>>16&15]+n[t>>12&15]+n[t>>8&15]+n[t>>4&15]+n[15&t]+n[h>>28&15]+n[h>>24&15]+n[h>>20&15]+n[h>>16&15]+n[h>>12&15]+n[h>>8&15]+n[h>>4&15]+n[15&h]+n[i>>28&15]+n[i>>24&15]+n[i>>20&15]+n[i>>16&15]+n[i>>12&15]+n[i>>8&15]+n[i>>4&15]+n[15&i]+n[s>>28&15]+n[s>>24&15]+n[s>>20&15]+n[s>>16&15]+n[s>>12&15]+n[s>>8&15]+n[s>>4&15]+n[15&s]+n[e>>28&15]+n[e>>24&15]+n[e>>20&15]+n[e>>16&15]+n[e>>12&15]+n[e>>8&15]+n[e>>4&15]+n[15&e]+n[r>>28&15]+n[r>>24&15]+n[r>>20&15]+n[r>>16&15]+n[r>>12&15]+n[r>>8&15]+n[r>>4&15]+n[15&r]+n[o>>28&15]+n[o>>24&15]+n[o>>20&15]+n[o>>16&15]+n[o>>12&15]+n[o>>8&15]+n[o>>4&15]+n[15&o];return this.is224||(f+=n[a>>28&15]+n[a>>24&15]+n[a>>20&15]+n[a>>16&15]+n[a>>12&15]+n[a>>8&15]+n[a>>4&15]+n[15&a]),f},t.prototype.toString=t.prototype.hex,t.prototype.digest=function(){this.finalize();var t=this.h0,h=this.h1,i=this.h2,s=this.h3,e=this.h4,r=this.h5,n=this.h6,o=this.h7,a=[t>>24&255,t>>16&255,t>>8&255,255&t,h>>24&255,h>>16&255,h>>8&255,255&h,i>>24&255,i>>16&255,i>>8&255,255&i,s>>24&255,s>>16&255,s>>8&255,255&s,e>>24&255,e>>16&255,e>>8&255,255&e,r>>24&255,r>>16&255,r>>8&255,255&r,n>>24&255,n>>16&255,n>>8&255,255&n];return this.is224||a.push(o>>24&255,o>>16&255,o>>8&255,255&o),a},t.prototype.array=t.prototype.digest,t.prototype.arrayBuffer=function(){this.finalize();var t=new ArrayBuffer(this.is224?28:32),h=new DataView(t);return h.setUint32(0,this.h0),h.setUint32(4,this.h1),h.setUint32(8,this.h2),h.setUint32(12,this.h3),h.setUint32(16,this.h4),h.setUint32(20,this.h5),h.setUint32(24,this.h6),this.is224||h.setUint32(28,this.h7),t};var l=d();l.sha256=l,l.sha224=d(!0),s?module.exports=l:(h.sha256=l.sha256,h.sha224=l.sha224,e&&define(function(){return l}))
