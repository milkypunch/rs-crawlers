

function get_enviroment(proxy_array) {
    for(var i=0; i<proxy_array.length; i++){
        handler = '{\n' +
            '    get: function(target, property, receiver) {\n' +
            '        console.log("方法:", "get  ", "对象名称:", ' +
            '"' + proxy_array[i] + '" ,' +
            '"  属性名称:", property, ' +
            // '"  属性名称类型:", ' + 'typeof property, ' +
            // '"  属性值:", ' + 'target[property], ' +
            '"  属性值类型:", typeof target[property]);\n' +
            '        return target[property];\n' +
            '    },\n' +
            '    set: function(target, property, value, receiver) {\n' +
            '        console.log("方法:", "set  ", "对象名称:", ' +
            '"' + proxy_array[i] + '" ,' +
            '"  属性名称:", property, ' +
            // '"  属性名称类型:", ' + 'typeof property, ' +
            // '"  属性值:", ' + 'target[property], ' +
            '"  属性值类型:", typeof target[property]);\n' +
            '        return Reflect.set(...arguments);\n' +
            '    }\n' +
            '}'
        eval('try{\n' + proxy_array[i] + ';\n'
        + proxy_array[i] + '=new Proxy(' + proxy_array[i] + ', ' + handler + ')}catch (e) {\n' + proxy_array[i] + '={};\n'
        + proxy_array[i] + '=new Proxy(' + proxy_array[i] + ', ' + handler + ')}')
    }
}
proxy_array = ['window', 'document', 'location', 'navigator', 'history','screen', 'Element']

content = "content_value"; 

delete __filename;
delete __dirname;


var _null = function() {
    console.log(arguments)
};
CSSStyleDeclaration = function() {};
window = global;
window.top = window;
window.self = window;
window.name = '';
window.indexedDB = {};
window.localStorage = {
    removeItem: _null,
    getItem: _null
};
window.globalStorage = undefined;
window.sessionStorage = {
    getItem: _null
};


window.chrome = {
    "app": {
        "isInstalled": false,
        "InstallState": {
            "DISABLED": "disabled",
            "INSTALLED": "installed",
            "NOT_INSTALLED": "not_installed"
        },
        "RunningState": {
            "CANNOT_RUN": "cannot_run",
            "READY_TO_RUN": "ready_to_run",
            "RUNNING": "running"
        }
    }
}
window.innerHeight = 797;
window.innerWidth = 1470;
window.outerHeight = 797;
window.outerWidth = 1470;

// window.execScript = undefined;
window.ActiveXObject = undefined;
window.TEMPORARY = 0;
window.PointerEvent = _null;
window.CanvasRenderingContext2D = _null;
window.HTMLCanvasElement = _null;
window.WebSocket = _null;
window.webkitRequestFileSystem = _null;

window.navigator = {
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    platform: 'MacIntel',
    getBattery: _null,
    connection: {},
    appVersion: '5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}
navigator.webkitPersistentStorage = {};

window.DOMParser = function() {};
Object.defineProperty(DOMParser.prototype, "parseFromString", {
    "writable": true,
    "enumerable": true,
    "configurable": true,
    "value": function parseFromString() {} 
    })
window.XMLHttpRequest = _null; 
window.addEventListener = _null;
window.attachEvent = undefined;
location = {
    "ancestorOrigins": {},
    "href": "https://qikan.cqvip.com/Qikan/Journal/JournalGuid?from=index",
    "origin": "https://qikan.cqvip.com",
    "protocol": "https:",
    "host": "qikan.cqvip.com",
    "hostname": "qikan.cqvip.com",
    "port": "",
    "pathname": "/Qikan/Journal/JournalGuid",
    "search": "?from=index",
    "hash": ""
}
history = {
    replaceState: _null
}
div = {
    getElementsByTagName: function(a) {
        if (a=='i') {
            return {length:0};
        }
    }
};

meta = {
    parentNode: {
        removeChild: function(arg) {
            console.log("removeChild: ", arg)
        }
    },
    getAttribute: function(a) {
        console.log("getAttribute: ", a);
        if (a=='r') {
            return "m";
        }
    },
    content: content
}

document = {
    createElement: function(a) {
        console.log("createElement params: ", a)
        if (a=="div") {
            return div;
        }
        if (a === "a"){
            return  {}
        }
        if(a ==="form"){
            return  {}
        }
    },
    appendChild: _null,
    removeChild: _null,
    getElementsByTagName: function(arg) {
        console.log("getElementsByTagName: ", arg)
        if (arg=="script") {
            return {}
        //     // return [script, script] 
        }
        if (arg=="base") {
            return {}
        }
        if (arg=="meta") {
            return [meta, meta]
        } 
        if (arg=="__anchor__") {
            return null;
        }
    },
    getElementById: _null,
    visibilityState: 'visible',
    documentElement: {}
};

window.setInterval = function() {};

get_enviroment(proxy_array)

"ts_code_str"; 

require("./8.外链测试.js")



function getCookie() {
    return document.cookie
}
         