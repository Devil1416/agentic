// main.js
var mask = document.getElementById('mask');

function changeMaskProperties() {
    var r = Math.floor(Math.random() * 256);
    var g = Math.floor(Math.random() * 256);
    var b = Math.floor(Math.random() * 256);
    var color = 'rgb(' + r + ', ' + g + ', ' + b + ')';
    
    mask.style.backgroundColor = color;
    mask.style.opacity = Math.random();
    mask.style.width = (Math.floor(Math.random() * 300) + 100) + 'px';
    mask.style.height = (Math.floor(Math.random() * 300) + 100) + 'px';
}

setInterval(changeMaskProperties, 500); // Change every 500 milliseconds