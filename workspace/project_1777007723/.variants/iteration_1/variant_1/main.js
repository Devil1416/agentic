// main.js
var mask = document.getElementById('mask'); // Assuming the mask element has an id of 'mask' in your HTML

function changeMaskProperties() {
    var r = Math.floor(Math.random() * 256);
    var g = Math.floor(Math.random() * 256);
    var b = Math.floor(Math.random() * 256);
    var color = 'rgb(' + r + ', ' + g + ', ' + b + ')';
    
    mask.style.backgroundColor = color; // Change the background color of the mask to a random RGB value
    
    var opacity = Math.random(); // Generate a random opacity value
    mask.style.opacity = opacity; 
}

setInterval(changeMaskProperties, 100); // Call changeMaskProperties every 100 milliseconds