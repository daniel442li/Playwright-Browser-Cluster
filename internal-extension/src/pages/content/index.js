console.log('Content Script!!');

document.addEventListener('click', function(e) {
    const dot = document.createElement('div');
    dot.style.position = 'absolute';
    dot.style.width = '10px';
    dot.style.height = '10px';
    dot.style.backgroundColor = 'red';
    dot.style.borderRadius = '50%';
    dot.style.pointerEvents = 'none'; // Ensure the dot does not interfere with other interactions
    dot.style.left = `${e.pageX - 5}px`; // Center the dot on the cursor
    dot.style.top = `${e.pageY - 5}px`; // Adjust so the center of the dot matches the click point
    dot.style.zIndex = '999999'; // Set a high z-index value to ensure it appears above everything

    document.body.appendChild(dot);

    // Fade out the dot
    let opacity = 1;
    const fadeInterval = setInterval(function() {
      if (opacity <= 0.1) {
        clearInterval(fadeInterval);
        document.body.removeChild(dot);
      }
      dot.style.opacity = opacity;
      opacity -= opacity * 0.1;
    }, 50);
});