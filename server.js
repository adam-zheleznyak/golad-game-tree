'use strict';

const PORT = process.env.PORT || 5000;

var express = require('express');
var app = express();
var path = require('path');
var compression = require('compression');
var fs = require('fs');
var unzip = require('unzip');

fs.createReadStream('zip/gameTrees.zip').pipe(unzip.Extract({ path: 'public' }));

app.get('/', function(req,res) {
	res.sendFile(path.join(__dirname + '/GOLAD_Sample_Game_Trees.html'));
});

app.use(compression());

app.use(express.static('public'));

app.listen(PORT, function() {
	console.log("Listening on port " + PORT);
});